from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import Client
from team_management.models import Team, League, Player, Match
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = "執行基本前端(後端端點)煙霧測試：建立範例資料並模擬三種角色登入與關鍵頁面載入。"

    def handle(self, *args, **options):
        report = []

        # 建立/取得使用者
        admin, _ = User.objects.get_or_create(username='smoke_admin', defaults={
            'user_type': 'admin', 'is_approved': True
        })
        if not admin.check_password('adminpass'):
            admin.set_password('adminpass'); admin.is_approved = True; admin.save()

        coach, _ = User.objects.get_or_create(username='smoke_coach', defaults={
            'user_type': 'coach', 'is_approved': True
        })
        if not coach.check_password('coachpass'):
            coach.set_password('coachpass'); coach.is_approved = True; coach.save()

        player_user, _ = User.objects.get_or_create(username='smoke_player', defaults={
            'user_type': 'player', 'is_approved': True
        })
        if not player_user.check_password('playerpass'):
            player_user.set_password('playerpass'); player_user.is_approved = True; player_user.save()

        # 建立球隊/聯賽/球員/比賽
        team, _ = Team.objects.get_or_create(name='Smoke Team', defaults={'coach': coach, 'group': '成人組'})
        if team.coach != coach:
            team.coach = coach; team.save()

        league, _ = League.objects.get_or_create(
            name='Smoke League', season='2025', group='成人組', defaults={
                'start_date': date.today(), 'end_date': date.today(), 'coach': coach
            }
        )
        if league.coach != coach:
            league.coach = coach; league.save()

        player, _ = Player.objects.get_or_create(
            user=player_user,
            defaults={
                'nickname': 'SmokePlayer',
                'team': team,
                'jersey_number': 99,
                'positions': 'FW',
                'height': 170,
                'weight': 60,
                'age': 18,
                'stamina': '優',
                'speed': '優',
                'technique': '優'
            }
        )
        if player.team != team:
            player.team = team; player.save()

        Match.objects.get_or_create(
            league=league,
            team=team,
            opponent_name='Opp Smoke',
            match_date=timezone.now() + timedelta(days=1),
            venue='Smoke Field',
            status='scheduled'
        )

        pages_by_role = {
            'admin': ['/dashboard/', '/dashboard/statistics/', '/dashboard/matches/'],
            'coach': ['/dashboard/', '/dashboard/statistics/', '/dashboard/matches/'],
            'player': ['/dashboard/', '/dashboard/statistics/', '/dashboard/my-matches/'],
        }

        creds = [
            ('admin', 'smoke_admin', 'adminpass'),
            ('coach', 'smoke_coach', 'coachpass'),
            ('player', 'smoke_player', 'playerpass'),
        ]

        for role, username, password in creds:
            c = Client()
            logged_in = c.login(username=username, password=password)
            if not logged_in:
                report.append(f"[FAIL] {role} 無法登入")
                continue
            report.append(f"[OK] {role} 登入成功")
            # 健康檢查端點
            if role == 'admin':
                h = c.get('/healthz')
                if h.status_code == 200 and h.json().get('status') == 'ok':
                    report.append('  [OK] /healthz')
                else:
                    report.append(f"  [FAIL] /healthz {h.status_code}")
            for url in pages_by_role[role]:
                resp = c.get(url)
                if resp.status_code == 200:
                    report.append(f"  [OK] GET {url} 200")
                else:
                    report.append(f"  [FAIL] GET {url} {resp.status_code}")

            # 針對特定角色進行額外互動測試
            if role == 'coach':
                # 建立新球隊
                resp_team = c.post('/dashboard/teams/create/', {
                    'name': 'Smoke Team 2',
                    'group': '成人組',
                    'description': 'Created via smoke test'
                })
                if resp_team.status_code not in (200, 302):
                    report.append(f"  [FAIL] 建立球隊 回應碼 {resp_team.status_code}")
                else:
                    report.append("  [OK] 建立球隊提交")

                # 建立新聯賽
                resp_league = c.post('/dashboard/leagues/create/', {
                    'name': 'Smoke League 2',
                    'season': '2025',
                    'group': '成人組',
                    'start_date': date.today().strftime('%Y-%m-%d'),
                    'end_date': date.today().strftime('%Y-%m-%d'),
                    'description': 'Smoke league'
                })
                if resp_league.status_code not in (200, 302):
                    report.append(f"  [FAIL] 建立聯賽 回應碼 {resp_league.status_code}")
                else:
                    report.append("  [OK] 建立聯賽提交")

                # 抓取最新聯賽與球隊建立比賽
                latest_league = League.objects.order_by('-id').first()
                latest_team = Team.objects.order_by('-id').first()
                resp_match = c.post('/dashboard/matches/create/', {
                    'league': latest_league.id,
                    'team': latest_team.id,
                    'opponent_name': 'Form Opp',
                    'match_date': (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
                    'venue': 'Form Venue',
                    'status': 'scheduled'
                })
                if resp_match.status_code not in (200, 302):
                    report.append(f"  [FAIL] 建立比賽 回應碼 {resp_match.status_code}")
                else:
                    report.append("  [OK] 建立比賽提交")

            if role == 'player':
                # 取得可參加比賽並切換參與狀態
                matches_page = c.get('/dashboard/my-matches/')
                if matches_page.status_code == 200:
                    first_match = Match.objects.filter(team=player.team).first()
                    if first_match:
                        part_url = f'/dashboard/my-matches/{first_match.id}/participate/'
                        resp_toggle = c.post(part_url, {'is_participating': 'false'})
                        if resp_toggle.status_code not in (200, 302):
                            report.append(f"  [FAIL] 參與切換 回應碼 {resp_toggle.status_code}")
                        else:
                            report.append("  [OK] 參與狀態切換提交")
                    else:
                        report.append("  [WARN] 無比賽可供切換")
                else:
                    report.append("  [FAIL] 無法載入 my-matches 進行切換")

        self.stdout.write("\n==== 煙霧測試結果 ====")
        for line in report:
            self.stdout.write(line)
        failures = [r for r in report if '[FAIL]' in r]
        if failures:
            raise SystemExit("煙霧測試失敗: " + '; '.join(failures))
        self.stdout.write(self.style.SUCCESS('全部角色關鍵頁面載入成功。'))
