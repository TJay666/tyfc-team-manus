from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from .models import Team, Player, League, Match, PlayerStats, PlayerMatchParticipation
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse

User = get_user_model()

@login_required
def dashboard(request):
    context = {}
    
    # 基本統計
    if request.user.user_type == 'admin':
        context['total_users'] = User.objects.count()
        context['approved_users'] = User.objects.filter(is_approved=True).count()
        context['pending_users'] = User.objects.filter(is_approved=False)
    
    # 球隊數量統計 - 根據使用者類型調整
    if request.user.user_type == 'admin':
        context['total_teams'] = Team.objects.count()
    elif request.user.user_type == 'coach':
        context['total_teams'] = Team.objects.filter(coach=request.user).count()
    else:
        context['total_teams'] = 0  # 球員不顯示球隊數量
    context['upcoming_matches'] = Match.objects.filter(
        match_date__gte=timezone.now(),
        status='scheduled'
    ).count()
    
    # 教練專用資料
    if request.user.user_type == 'coach':
        context['my_teams'] = Team.objects.filter(coach=request.user)
        # 修改近期比賽查詢，包含更多資訊
        context['recent_matches'] = Match.objects.filter(
            Q(team__coach=request.user),
            match_date__gte=timezone.now() - timedelta(days=30)
        ).select_related('team', 'league').order_by('match_date')[:5]
    
    # 球員專用資料
    if request.user.user_type == 'player':
        try:
            player_profile = Player.objects.get(user=request.user)
            context['player_profile'] = player_profile
            
            # 球員近期比賽
            context['recent_matches'] = Match.objects.filter(
                team=player_profile.team,
                match_date__gte=timezone.now() - timedelta(days=30)
            ).select_related('team', 'league').order_by('match_date')[:5]
            
            # 球員統計
            stats = PlayerStats.objects.filter(player=player_profile).aggregate(
                total_matches=Count('match'),
                total_goals=Count('goals'),
                total_assists=Count('assists'),
                total_minutes=Count('minutes_played')
            )
            context['player_stats'] = stats
        except Player.DoesNotExist:
            context['player_profile'] = None
    
    return render(request, 'dashboard.html', context)

# Teams Views
@login_required
def teams(request):
    if request.user.user_type == 'admin':
        teams = Team.objects.all()
    elif request.user.user_type == 'coach':
        teams = Team.objects.filter(coach=request.user)
    else:
        messages.error(request, '您沒有權限查看此頁面。')
        return redirect('/dashboard/')
    
    return render(request, 'team_management/teams.html', {'teams': teams})

@login_required
def team_create(request):
    if request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        group = request.POST.get('group')
        description = request.POST.get('description', '')
        league_ids = request.POST.getlist('leagues')
        
        # 如果是教練，自動設定為自己
        if request.user.user_type == 'coach':
            coach = request.user
        else:
            coach_id = request.POST.get('coach')
            coach = get_object_or_404(User, id=coach_id, user_type='coach')
        
        team = Team.objects.create(
            name=name,
            coach=coach,
            group=group,
            description=description
        )
        
        # 添加參加聯賽
        if league_ids:
            leagues = League.objects.filter(id__in=league_ids)
            team.leagues.set(leagues)
        
        messages.success(request, f'球隊 {team.name} 建立成功！')
        return redirect('/dashboard/teams/')
    
    # 如果是管理員，提供教練選擇
    coaches = User.objects.filter(user_type='coach', is_approved=True) if request.user.user_type == 'admin' else None
    
    # 獲取可選的聯賽
    if request.user.user_type == 'admin':
        leagues = League.objects.all()
    else:
        leagues = League.objects.filter(coach=request.user)
    
    return render(request, 'team_management/team_form.html', {
        'coaches': coaches,
        'leagues': leagues,
        'action': 'create'
    })

@login_required
def team_edit(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    
    # 權限檢查
    if request.user.user_type == 'coach' and team.coach != request.user:
        messages.error(request, '您只能編輯自己的球隊。')
        return redirect('/dashboard/teams/')
    elif request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        team.name = request.POST.get('name')
        team.group = request.POST.get('group')
        team.description = request.POST.get('description', '')
        league_ids = request.POST.getlist('leagues')
        
        # 只有管理員可以更改教練
        if request.user.user_type == 'admin':
            coach_id = request.POST.get('coach')
            team.coach = get_object_or_404(User, id=coach_id, user_type='coach')
        
        team.save()
        
        # 更新參加聯賽
        if league_ids:
            leagues = League.objects.filter(id__in=league_ids)
            team.leagues.set(leagues)
        else:
            team.leagues.clear()
        
        messages.success(request, f'球隊 {team.name} 更新成功！')
        return redirect('/dashboard/teams/')
    
    coaches = User.objects.filter(user_type='coach', is_approved=True) if request.user.user_type == 'admin' else None
    
    # 獲取可選的聯賽
    if request.user.user_type == 'admin':
        leagues = League.objects.all()
    else:
        leagues = League.objects.filter(coach=request.user)
    
    return render(request, 'team_management/team_form.html', {
        'team': team,
        'coaches': coaches,
        'leagues': leagues,
        'action': 'edit'
    })

@login_required
def team_delete(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    
    # 權限檢查
    if request.user.user_type == 'coach' and team.coach != request.user:
        messages.error(request, '您只能刪除自己的球隊。')
        return redirect('/dashboard/teams/')
    elif request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        team_name = team.name
        team.delete()
        messages.success(request, f'球隊 {team_name} 已刪除。')
        return redirect('/dashboard/teams/')
    
    return render(request, 'team_management/team_confirm_delete.html', {'team': team})

# Players Views
@login_required
def players(request):
    if request.user.user_type == 'admin':
        players = Player.objects.all()
    elif request.user.user_type == 'coach':
        players = Player.objects.filter(team__coach=request.user)
    else:
        messages.error(request, '您沒有權限查看此頁面。')
        return redirect('/dashboard/')
    
    return render(request, 'team_management/players.html', {'players': players})

@login_required
def player_create(request):
    if request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        user_id = request.POST.get('user')
        nickname = request.POST.get('nickname')
        team_id = request.POST.get('team')
        jersey_number = request.POST.get('jersey_number') or None
        positions = request.POST.getlist('positions')
        height = request.POST.get('height') or None
        weight = request.POST.get('weight') or None
        age = request.POST.get('age')
        stamina = request.POST.get('stamina')
        speed = request.POST.get('speed')
        technique = request.POST.get('technique')
        
        user = get_object_or_404(User, id=user_id, user_type='player')
        team = get_object_or_404(Team, id=team_id)
        
        # 權限檢查
        if request.user.user_type == 'coach' and team.coach != request.user:
            messages.error(request, '您只能為自己的球隊新增球員。')
            return redirect('/dashboard/players/')
        
        # 檢查球衣號碼是否重複（如果有提供）
        if jersey_number and Player.objects.filter(team=team, jersey_number=jersey_number).exists():
            messages.error(request, f'球衣號碼 {jersey_number} 在此球隊已被使用。')
            return render(request, 'team_management/player_form.html', {
                'teams': Team.objects.filter(coach=request.user) if request.user.user_type == 'coach' else Team.objects.all(),
                'users': User.objects.filter(user_type='player', is_approved=True),
                'action': 'create'
            })
        
        # 檢查位置是否有選擇
        if not positions:
            messages.error(request, '請至少選擇一個位置。')
            return render(request, 'team_management/player_form.html', {
                'teams': Team.objects.filter(coach=request.user) if request.user.user_type == 'coach' else Team.objects.all(),
                'users': User.objects.filter(user_type='player', is_approved=True),
                'action': 'create'
            })
        
        player = Player.objects.create(
            user=user,
            nickname=nickname,
            team=team,
            jersey_number=jersey_number,
            positions=','.join(positions),
            height=height,
            weight=weight,
            age=age,
            stamina=stamina,
            speed=speed,
            technique=technique
        )
        
        # 為新球員創建參加該球隊所有現有比賽的記錄
        team_matches = Match.objects.filter(team=team)
        for match in team_matches:
            PlayerMatchParticipation.objects.get_or_create(
                player=player,
                match=match,
                defaults={'is_participating': True}
            )
        
        messages.success(request, f'球員 {player.nickname} 建立成功！已設定預設參加所有比賽。')
        return redirect('/dashboard/players/')
    
    teams = Team.objects.filter(coach=request.user) if request.user.user_type == 'coach' else Team.objects.all()
    users = User.objects.filter(user_type='player', is_approved=True)
    
    return render(request, 'team_management/player_form.html', {
        'teams': teams,
        'users': users,
        'action': 'create'
    })

@login_required
def player_edit(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    
    # 權限檢查
    if request.user.user_type == 'coach' and player.team.coach != request.user:
        messages.error(request, '您只能編輯自己球隊的球員。')
        return redirect('/dashboard/players/')
    elif request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        nickname = request.POST.get('nickname')
        team_id = request.POST.get('team')
        jersey_number = request.POST.get('jersey_number') or None
        positions = request.POST.getlist('positions')
        height = request.POST.get('height') or None
        weight = request.POST.get('weight') or None
        age = request.POST.get('age')
        stamina = request.POST.get('stamina')
        speed = request.POST.get('speed')
        technique = request.POST.get('technique')
        
        team = get_object_or_404(Team, id=team_id)
        
        # 權限檢查
        if request.user.user_type == 'coach' and team.coach != request.user:
            messages.error(request, '您只能將球員分配到自己的球隊。')
            return redirect('/dashboard/players/')
        
        # 檢查球衣號碼是否重複（排除自己，如果有提供）
        if jersey_number and Player.objects.filter(team=team, jersey_number=jersey_number).exclude(id=player.id).exists():
            messages.error(request, f'球衣號碼 {jersey_number} 在此球隊已被使用。')
            teams = Team.objects.filter(coach=request.user) if request.user.user_type == 'coach' else Team.objects.all()
            return render(request, 'team_management/player_form.html', {
                'player': player,
                'teams': teams,
                'action': 'edit'
            })
        
        # 檢查位置是否有選擇
        if not positions:
            messages.error(request, '請至少選擇一個位置。')
            teams = Team.objects.filter(coach=request.user) if request.user.user_type == 'coach' else Team.objects.all()
            return render(request, 'team_management/player_form.html', {
                'player': player,
                'teams': teams,
                'action': 'edit'
            })
        
        player.nickname = nickname
        player.team = team
        player.jersey_number = jersey_number
        player.positions = ','.join(positions)
        player.height = height
        player.weight = weight
        player.age = age
        player.stamina = stamina
        player.speed = speed
        player.technique = technique
        player.save()
        
        messages.success(request, f'球員 {player.nickname} 更新成功！')
        return redirect('/dashboard/players/')
    
    teams = Team.objects.filter(coach=request.user) if request.user.user_type == 'coach' else Team.objects.all()
    
    return render(request, 'team_management/player_form.html', {
        'player': player,
        'teams': teams,
        'action': 'edit'
    })

@login_required
def player_delete(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    
    # 權限檢查
    if request.user.user_type == 'coach' and player.team.coach != request.user:
        messages.error(request, '您只能刪除自己球隊的球員。')
        return redirect('/dashboard/players/')
    elif request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        player_name = player.user.username
        player.delete()
        messages.success(request, f'球員 {player_name} 已刪除。')
        return redirect('/dashboard/players/')
    
    return render(request, 'team_management/player_confirm_delete.html', {'player': player})

# Leagues Views
@login_required
def leagues(request):
    if request.user.user_type == "admin":
        leagues = League.objects.all()
    elif request.user.user_type == "coach":
        leagues = League.objects.filter(coach=request.user)
    else:
        messages.error(request, "您沒有權限查看此頁面。")
        return redirect("/dashboard/")

    return render(request, "team_management/leagues.html", {"leagues": leagues})

@login_required
def league_create(request):
    if request.user.user_type not in ["admin", "coach"]:
        messages.error(request, "您沒有權限執行此操作。")
        return redirect("/dashboard/")

    if request.method == "POST":
        name = request.POST.get("name")
        season = request.POST.get("season")
        group = request.POST.get("group")
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")
        description = request.POST.get("description", "")

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, '日期格式錯誤，請使用 YYYY-MM-DD 格式。')
            coaches = User.objects.filter(user_type="coach", is_approved=True) if request.user.user_type == "admin" else None
            return render(request, "team_management/league_form.html", {
                "coaches": coaches,
                "action": "create"
            })

        if request.user.user_type == "coach":
            coach = request.user
        else:
            coach_id = request.POST.get("coach")
            coach = get_object_or_404(User, id=coach_id, user_type="coach")

        league = League.objects.create(
            name=name,
            season=season,
            group=group,
            start_date=start_date,
            end_date=end_date,
            description=description,
            coach=coach
        )

        messages.success(request, f"聯賽 {league.name} 建立成功！")
        return redirect("/dashboard/leagues/")

    coaches = User.objects.filter(user_type="coach", is_approved=True) if request.user.user_type == "admin" else None

    return render(request, "team_management/league_form.html", {
        "coaches": coaches,
        "action": "create"
    })

@login_required
def league_edit(request, league_id):
    league = get_object_or_404(League, id=league_id)

    # 權限檢查
    if request.user.user_type == "coach" and league.coach != request.user:
        messages.error(request, "您只能編輯自己負責的聯賽。")
        return redirect("/dashboard/leagues/")
    elif request.user.user_type not in ["admin", "coach"]:
        messages.error(request, "您沒有權限執行此操作。 ")
        return redirect("/dashboard/")

    if request.method == "POST":
        name = request.POST.get("name")
        season = request.POST.get("season")
        group = request.POST.get("group")
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")
        description = request.POST.get("description", "")

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, '日期格式錯誤，請使用 YYYY-MM-DD 格式。')
            coaches = User.objects.filter(user_type="coach", is_approved=True) if request.user.user_type == "admin" else None
            return render(request, "team_management/league_form.html", {
                "league": league,
                "coaches": coaches,
                "action": "edit"
            })

        if request.user.user_type == "admin":
            coach_id = request.POST.get("coach")
            coach = get_object_or_404(User, id=coach_id, user_type="coach")
            league.coach = coach

        league.name = name
        league.season = season
        league.group = group
        league.start_date = start_date
        league.end_date = end_date
        league.description = description
        league.save()

        messages.success(request, f"聯賽 {league.name} 更新成功！")
        return redirect("/dashboard/leagues/")

    coaches = User.objects.filter(user_type="coach", is_approved=True) if request.user.user_type == "admin" else None

    return render(request, "team_management/league_form.html", {
        "league": league,
        "coaches": coaches,
        "action": "edit"
    })

@login_required
def league_delete(request, league_id):
    league = get_object_or_404(League, id=league_id)

    # 權限檢查
    if request.user.user_type == "coach" and league.coach != request.user:
        messages.error(request, "您只能刪除自己負責的聯賽。")
        return redirect("/dashboard/leagues/")
    elif request.user.user_type not in ["admin", "coach"]:
        messages.error(request, "您沒有權限執行此操作。")
        return redirect("/dashboard/")

    if request.method == "POST":
        league_name = league.name
        league.delete()
        messages.success(request, f"聯賽 {league_name} 已刪除。 ")
        return redirect("/dashboard/leagues/")

    return render(request, "team_management/league_confirm_delete.html", {"league": league})

# Matches Views
@login_required
def matches(request):
    if request.user.user_type == 'admin':
        matches = Match.objects.all()
    elif request.user.user_type == 'coach':
        matches = Match.objects.filter(Q(league__coach=request.user) | Q(team__coach=request.user)).distinct()
    else:
        messages.error(request, '您沒有權限查看此頁面。')
        return redirect('/dashboard/')
    
    return render(request, 'team_management/matches.html', {'matches': matches})

@login_required
def match_create(request):
    if request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        league_id = request.POST.get('league')
        team_id = request.POST.get('team')
        opponent_name = request.POST.get('opponent_name')
        match_date_str = request.POST.get('match_date')
        venue = request.POST.get('venue')
        our_score = request.POST.get('our_score') or None
        opponent_score = request.POST.get('opponent_score') or None
        status = request.POST.get('status', 'scheduled')  # 設置默認值為'scheduled'
        notes = request.POST.get('notes', '')
        
        league = get_object_or_404(League, id=league_id)
        team = get_object_or_404(Team, id=team_id)
        
        # 直接使用match_date_str，不進行格式檢查
        match = Match.objects.create(
            league=league,
            team=team,
            opponent_name=opponent_name,
            match_date=match_date_str,
            venue=venue,
            our_score=our_score,
            opponent_score=opponent_score,
            status=status,
            notes=notes
        )
        
        # 為該球隊的所有球員創建預設參加的記錄
        team_players = Player.objects.filter(team=team)
        for player in team_players:
            PlayerMatchParticipation.objects.get_or_create(
                player=player,
                match=match,
                defaults={'is_participating': True}
            )
        
        messages.success(request, f'比賽 {match.opponent_name} 建立成功！已為所有球員設定預設參加。')
        return redirect('/dashboard/matches/')
    
    leagues = League.objects.filter(coach=request.user) if request.user.user_type == 'coach' else League.objects.all()
    teams = Team.objects.filter(coach=request.user) if request.user.user_type == 'coach' else Team.objects.all()
    
    return render(request, 'team_management/match_form.html', {
        'leagues': leagues,
        'teams': teams,
        'action': 'create'
    })

@login_required
def match_edit(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    # 權限檢查
    if request.user.user_type == 'coach' and match.league.coach != request.user:
        messages.error(request, '您只能編輯自己負責聯賽的比賽。')
        return redirect('/dashboard/matches/')
    elif request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        league_id = request.POST.get('league')
        team_id = request.POST.get('team')
        opponent_name = request.POST.get('opponent_name')
        match_date_str = request.POST.get('match_date')
        venue = request.POST.get('venue')
        our_score = request.POST.get('our_score') or None
        opponent_score = request.POST.get('opponent_score') or None
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        league = get_object_or_404(League, id=league_id)
        team = get_object_or_404(Team, id=team_id)
        
        match.league = league
        match.team = team
        match.opponent_name = opponent_name
        match.match_date = match_date_str
        match.venue = venue
        match.our_score = our_score
        match.opponent_score = opponent_score
        match.status = status
        match.notes = notes
        match.save()
        
        messages.success(request, f'比賽 {match.opponent_name} 更新成功！')
        return redirect('/dashboard/matches/')
    
    leagues = League.objects.filter(coach=request.user) if request.user.user_type == 'coach' else League.objects.all()
    teams = Team.objects.filter(coach=request.user) if request.user.user_type == 'coach' else Team.objects.all()
    
    return render(request, 'team_management/match_form.html', {
        'match': match,
        'leagues': leagues,
        'teams': teams,
        'action': 'edit'
    })

@login_required
def match_delete(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    # 權限檢查
    if request.user.user_type == 'coach' and match.league.coach != request.user:
        messages.error(request, '您只能刪除自己負責聯賽的比賽。')
        return redirect('/dashboard/matches/')
    elif request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        match_info = match.opponent_name
        match.delete()
        messages.success(request, f'比賽 {match_info} 已刪除。')
        return redirect('/dashboard/matches/')
    
    return render(request, 'team_management/match_confirm_delete.html', {'match': match})

@login_required
def match_participants(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    # 權限檢查
    if request.user.user_type == 'coach' and match.team.coach != request.user:
        messages.error(request, '您只能查看自己球隊的比賽參與情況。')
        return redirect('/dashboard/matches/')
    elif request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    # 處理POST請求 - 更新球員數據
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('player_'):
                parts = key.split('_')
                if len(parts) == 3:
                    player_id = parts[1]
                    field_name = parts[2]
                    
                    try:
                        player = Player.objects.get(id=player_id, team=match.team)
                        
                        # 獲取或創建PlayerStats記錄
                        player_stats, created = PlayerStats.objects.get_or_create(
                            player=player,
                            match=match,
                            defaults={
                                'goals': 0,
                                'assists': 0,
                                'yellow_cards': 0,
                                'red_cards': 0,
                                'minutes_played': 0
                            }
                        )
                        
                        # 更新對應欄位
                        if field_name in ['goals', 'assists', 'yellow_cards', 'red_cards', 'minutes_played']:
                            setattr(player_stats, field_name, int(value) if value else 0)
                            player_stats.save()
                    
                    except (Player.DoesNotExist, ValueError):
                        continue
        
        messages.success(request, '球員數據已更新成功！')
        return redirect(f'/dashboard/matches/{match_id}/participants/')
    
    # 獲取該比賽的所有參與記錄
    participations = PlayerMatchParticipation.objects.filter(match=match)
    
    # 獲取該球隊的所有球員
    team_players = Player.objects.filter(team=match.team)
    
    # 為每個球員添加參與狀態和統計數據
    for player in team_players:
        try:
            participation = participations.get(player=player)
            player.is_participating = participation.is_participating
        except PlayerMatchParticipation.DoesNotExist:
            # 如果沒有參與記錄，創建一個預設為參加的記錄
            PlayerMatchParticipation.objects.create(
                player=player,
                match=match,
                is_participating=True
            )
            player.is_participating = True
        
        # 獲取球員在此比賽的統計數據
        try:
            stats = PlayerStats.objects.get(player=player, match=match)
            player.goals = stats.goals
            player.assists = stats.assists
            player.yellow_cards = stats.yellow_cards
            player.red_cards = stats.red_cards
            player.minutes_played = stats.minutes_played
        except PlayerStats.DoesNotExist:
            player.goals = 0
            player.assists = 0
            player.yellow_cards = 0
            player.red_cards = 0
            player.minutes_played = 0
    
    return render(request, 'team_management/match_participants.html', {
        'match': match,
        'players': team_players
    })

# Player Stats Views
@login_required
def player_stats(request):
    if request.user.user_type == 'admin':
        stats = PlayerStats.objects.all()
    elif request.user.user_type == 'coach':
        stats = PlayerStats.objects.filter(player__team__coach=request.user)
    else:
        messages.error(request, '您沒有權限查看此頁面。')
        return redirect('/dashboard/')
    
    return render(request, 'team_management/player_stats.html', {'stats': stats})

@login_required
def player_stats_create(request):
    if request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        player_id = request.POST.get('player')
        match_id = request.POST.get('match')
        goals = request.POST.get('goals') or 0
        assists = request.POST.get('assists') or 0
        minutes_played = request.POST.get('minutes_played') or 0
        
        player = get_object_or_404(Player, id=player_id)
        match = get_object_or_404(Match, id=match_id)
        
        # 權限檢查
        if request.user.user_type == 'coach' and (player.team.coach != request.user or match.league.coach != request.user):
            messages.error(request, '您只能為自己球隊的球員和自己負責聯賽的比賽新增統計數據。')
            return redirect('/dashboard/player_stats/')
        
        stats = PlayerStats.objects.create(
            player=player,
            match=match,
            goals=goals,
            assists=assists,
            minutes_played=minutes_played
        )
        
        messages.success(request, '球員統計數據建立成功！')
        return redirect('/dashboard/player_stats/')
    
    players = Player.objects.filter(team__coach=request.user) if request.user.user_type == 'coach' else Player.objects.all()
    matches = Match.objects.filter(league__coach=request.user) if request.user.user_type == 'coach' else Match.objects.all()
    
    return render(request, 'team_management/player_stats_form.html', {
        'players': players,
        'matches': matches,
        'action': 'create'
    })

@login_required
def player_stats_edit(request, stats_id):
    stats = get_object_or_404(PlayerStats, id=stats_id)
    
    # 權限檢查
    if request.user.user_type == 'coach' and (stats.player.team.coach != request.user or stats.match.league.coach != request.user):
        messages.error(request, '您只能編輯自己球隊的球員和自己負責聯賽的比賽統計數據。')
        return redirect('/dashboard/player_stats/')
    elif request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        player_id = request.POST.get('player')
        match_id = request.POST.get('match')
        goals = request.POST.get('goals') or 0
        assists = request.POST.get('assists') or 0
        minutes_played = request.POST.get('minutes_played') or 0
        
        player = get_object_or_404(Player, id=player_id)
        match = get_object_or_404(Match, id=match_id)
        
        # 權限檢查
        if request.user.user_type == 'coach' and (player.team.coach != request.user or match.league.coach != request.user):
            messages.error(request, '您只能將統計數據分配給自己球隊的球員和自己負責聯賽的比賽。')
            return redirect('/dashboard/player_stats/')
        
        stats.player = player
        stats.match = match
        stats.goals = goals
        stats.assists = assists
        stats.minutes_played = minutes_played
        stats.save()
        
        messages.success(request, '球員統計數據更新成功！')
        return redirect('/dashboard/player_stats/')
    
    players = Player.objects.filter(team__coach=request.user) if request.user.user_type == 'coach' else Player.objects.all()
    matches = Match.objects.filter(league__coach=request.user) if request.user.user_type == 'coach' else Match.objects.all()
    
    return render(request, 'team_management/player_stats_form.html', {
        'stats': stats,
        'players': players,
        'matches': matches,
        'action': 'edit'
    })

@login_required
def player_stats_delete(request, stats_id):
    stats = get_object_or_404(PlayerStats, id=stats_id)
    
    # 權限檢查
    if request.user.user_type == 'coach' and (stats.player.team.coach != request.user or stats.match.league.coach != request.user):
        messages.error(request, '您只能刪除自己球隊的球員和自己負責聯賽的比賽統計數據。')
        return redirect('/dashboard/player_stats/')
    elif request.user.user_type not in ['admin', 'coach']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        stats.delete()
        messages.success(request, '球員統計數據已刪除。')
        return redirect('/dashboard/player_stats/')
    
    return render(request, 'team_management/player_stats_confirm_delete.html', {'stats': stats})

# User Management Views
@login_required
def user_management(request):
    if request.user.user_type != 'admin':
        messages.error(request, '您沒有權限查看此頁面。')
        return redirect('/dashboard/')
    
    users = User.objects.all().order_by('date_joined')
    return render(request, 'accounts/user_management.html', {'users': users})

@login_required
def approve_user(request, user_id):
    if request.user.user_type != 'admin':
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    user_to_approve = get_object_or_404(User, id=user_id)
    user_to_approve.is_approved = True
    user_to_approve.save()
    messages.success(request, f'用戶 {user_to_approve.username} 已批准。')
    return redirect('/dashboard/user_management/')

@login_required
def reject_user(request, user_id):
    if request.user.user_type != 'admin':
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('/dashboard/')
    
    user_to_reject = get_object_or_404(User, id=user_id)
    user_to_reject.delete()
    messages.success(request, f'用戶 {user_to_reject.username} 已拒絕並刪除。')
    return redirect('/dashboard/user_management/')

# 移除重複的user_edit函數，使用accounts應用中的edit_user函數




@login_required
def statistics(request):
    """統計數據頁面 - 根據用戶類型顯示相應的統計數據"""
    context = {}
    
    if request.user.user_type == 'admin':
        # 管理員可以看到所有數據
        context['total_teams'] = Team.objects.count()
        context['total_players'] = Player.objects.count()
        context['total_matches'] = Match.objects.count()
        context['finished_matches'] = Match.objects.filter(status='completed').count()
        
        # 球隊統計
        teams = Team.objects.all()
        team_stats = []
        for team in teams:
            players_count = Player.objects.filter(team=team).count()
            matches = Match.objects.filter(team=team)
            matches_count = matches.count()
            
            # 計算勝負平 - 修正狀態過濾條件
            wins = 0
            losses = 0
            draws = 0
            for match in matches.filter(status__in=['completed', 'finished']):
                if match.our_score is not None and match.opponent_score is not None:
                    if match.our_score > match.opponent_score:
                        wins += 1
                    elif match.our_score < match.opponent_score:
                        losses += 1
                    else:
                        draws += 1
            
            # 創建帶有統計數據的team對象
            team.player_count = players_count
            team.total_matches = matches_count
            team.wins = wins
            team.losses = losses
            team.draws = draws
            team_stats.append(team)
        
        context['teams'] = team_stats
        
        # 組別分布數據
        from django.db.models import Count
        group_data = Team.objects.values('group').annotate(count=Count('group'))
        context['group_labels'] = [item['group'] for item in group_data]
        context['group_data'] = [item['count'] for item in group_data]
        
        # 比賽狀態分布數據
        match_status_data = Match.objects.values('status').annotate(count=Count('status'))
        status_mapping = {
            'scheduled': '已安排',
            'in_progress': '進行中',
            'completed': '已完成',
            'cancelled': '已取消'
        }
        context['match_status_labels'] = [status_mapping.get(item['status'], item['status']) for item in match_status_data]
        context['match_status_data'] = [item['count'] for item in match_status_data]
        
    elif request.user.user_type == 'coach':
        # 教練只能看到自己的球隊數據
        my_teams = Team.objects.filter(coach=request.user)
        context['my_teams_count'] = my_teams.count()
        context['my_players_count'] = Player.objects.filter(team__coach=request.user).count()
        context['my_matches_count'] = Match.objects.filter(team__coach=request.user).count()
        
        # 動態計算球隊統計
        team_stats = []
        for team in my_teams:
            players_count = Player.objects.filter(team=team).count()
            matches = Match.objects.filter(team=team)
            matches_count = matches.count()
            
            # 計算勝負平 - 修正狀態過濾條件
            wins = 0
            losses = 0
            draws = 0
            for match in matches.filter(status__in=['completed', 'finished']):
                if match.our_score is not None and match.opponent_score is not None:
                    if match.our_score > match.opponent_score:
                        wins += 1
                    elif match.our_score < match.opponent_score:
                        losses += 1
                    else:
                        draws += 1
            
            # 添加動態屬性
            team.player_count = players_count
            team.total_matches = matches_count
            team.wins = wins
            team.losses = losses
            team.draws = draws
            
        context['my_teams'] = my_teams
        
        # 球員統計
        players = Player.objects.filter(team__coach=request.user)
        player_statistics = []
        for player in players:
            stats = PlayerStats.objects.filter(player=player)
            matches_played = PlayerMatchParticipation.objects.filter(
                player=player, 
                is_participating=True,
                match__status='completed'
            ).count()
            
            total_goals = sum(stat.goals for stat in stats)
            total_assists = sum(stat.assists for stat in stats)
            total_yellow_cards = sum(stat.yellow_cards for stat in stats)
            total_red_cards = sum(stat.red_cards for stat in stats)
            total_minutes = sum(stat.minutes_played for stat in stats)
            
            player_statistics.append({
                'player': player,
                'matches_played': matches_played,
                'total_goals': total_goals,
                'total_assists': total_assists,
                'total_yellow_cards': total_yellow_cards,
                'total_red_cards': total_red_cards,
                'total_minutes': total_minutes
            })
        
        context['player_statistics'] = player_statistics
        
    elif request.user.user_type == 'player':
        # 球員只能看到自己的統計數據
        try:
            player = Player.objects.get(user=request.user)
            player_stats = PlayerStats.objects.filter(player=player)
            
            matches_played = PlayerMatchParticipation.objects.filter(
                player=player, 
                is_participating=True,
                match__status='completed'
            ).count()
            
            # 個人統計
            total_goals = sum(stats.goals for stats in player_stats)
            total_assists = sum(stats.assists for stats in player_stats)
            total_yellow_cards = sum(stats.yellow_cards for stats in player_stats)
            total_red_cards = sum(stats.red_cards for stats in player_stats)
            total_minutes = sum(stats.minutes_played for stats in player_stats)
            
            context['player_stats'] = {
                'matches_played': matches_played,
                'total_goals': total_goals,
                'total_assists': total_assists,
                'total_yellow_cards': total_yellow_cards,
                'total_red_cards': total_red_cards,
                'total_minutes': total_minutes
            }
            
            # 個人比賽記錄
            context['player_match_stats'] = PlayerStats.objects.filter(player=player).select_related('match')
            
        except Player.DoesNotExist:
            context['player_stats'] = {
                'matches_played': 0,
                'total_goals': 0,
                'total_assists': 0,
                'total_yellow_cards': 0,
                'total_red_cards': 0,
                'total_minutes': 0
            }
            context['player_match_stats'] = []
    
    return render(request, 'team_management/statistics.html', context)

@login_required
def my_matches(request):
    """球員查看自己可以參加的比賽"""
    if request.user.user_type != 'player':
        messages.error(request, '只有球員可以查看此頁面。')
        return redirect('/dashboard/')
    
    try:
        # 獲取當前用戶的球員資料
        player = Player.objects.get(user=request.user)
        
        # 獲取該球員所屬球隊的所有比賽
        team_matches = Match.objects.filter(team=player.team).order_by('match_date')
        
        # 獲取球員的參與狀態
        from django.utils import timezone
        current_time = timezone.now()
        
        for match in team_matches:
            try:
                participation = PlayerMatchParticipation.objects.get(player=player, match=match)
                match.is_participating = participation.is_participating
            except PlayerMatchParticipation.DoesNotExist:
                # 如果沒有記錄，創建一個預設為參加的記錄
                participation = PlayerMatchParticipation.objects.create(
                    player=player,
                    match=match,
                    is_participating=True
                )
                match.is_participating = True
            
            # 檢查是否可以修改（比賽時間未過期）
            match.can_edit = match.match_date > current_time
        
        return render(request, 'team_management/my_matches.html', {'matches': team_matches, 'player': player})
    
    except Player.DoesNotExist:
        messages.error(request, '找不到您的球員資料。')
        return redirect('/dashboard/')

@login_required
def match_participate(request, match_id):
    """球員設置是否參加比賽"""
    if request.user.user_type != 'player':
        messages.error(request, '只有球員可以執行此操作。')
        return redirect('/dashboard/')
    
    try:
        # 獲取當前用戶的球員資料
        player = Player.objects.get(user=request.user)
        match = Match.objects.get(id=match_id)
        
        # 確認比賽是否屬於球員的球隊
        if match.team != player.team:
            messages.error(request, '您不能參加其他球隊的比賽。')
            return redirect('/dashboard/my-matches/')
        
        # 檢查比賽時間是否已過期
        from django.utils import timezone
        current_time = timezone.now()
        if match.match_date <= current_time:
            messages.error(request, '比賽時間已過，無法修改參加狀態。')
            return redirect('/dashboard/my-matches/')
        
        if request.method == 'POST':
            is_participating = request.POST.get('is_participating') == 'true'
            
            # 更新或創建參與記錄
            participation, created = PlayerMatchParticipation.objects.update_or_create(
                player=player,
                match=match,
                defaults={'is_participating': is_participating}
            )
            
            if is_participating:
                messages.success(request, f'您已確認參加 {match.match_date.strftime("%Y-%m-%d %H:%M")} 的比賽。')
            else:
                messages.success(request, f'您已確認不參加 {match.match_date.strftime("%Y-%m-%d %H:%M")} 的比賽。')
            
            return redirect('/dashboard/my-matches/')
        
        # GET請求顯示確認頁面
        return render(request, 'team_management/match_participate.html', {'match': match})
    
    except Player.DoesNotExist:
        messages.error(request, '找不到您的球員資料。')
        return redirect('/dashboard/')
    except Match.DoesNotExist:
        messages.error(request, '找不到指定的比賽。')
        return redirect('/dashboard/my-matches/')

