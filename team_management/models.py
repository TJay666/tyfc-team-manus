from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Team(models.Model):
    name = models.CharField(max_length=100, verbose_name='球隊名稱')
    coach = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'coach'},
        verbose_name='教練'
    )
    group = models.CharField(
        max_length=50,
        choices=[
            ('幼兒組', '幼兒組'),
            ('國小組', '國小組'),
            ('國中組', '國中組'),
            ('高中組', '高中組'),
            ('成人組', '成人組'),
        ],
        verbose_name='組別'
    )
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    leagues = models.ManyToManyField('League', blank=True, related_name='participating_teams', verbose_name='參加聯賽')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    
    class Meta:
        verbose_name = '球隊'
        verbose_name_plural = '球隊'
    
    def __str__(self):
        return f"{self.name} ({self.group})"

class Player(models.Model):
    POSITION_CHOICES = [
        ('GK', '守門員'),
        ('DF', '後衛'),
        ('MF', '中場'),
        ('FW', '前鋒'),
    ]
    
    ABILITY_CHOICES = [
        ('優', '優'),
        ('佳', '佳'),
        ('普', '普'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='使用者')
    nickname = models.CharField(max_length=50, verbose_name='球員暱稱')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name='球隊')
    jersey_number = models.IntegerField(blank=True, null=True, verbose_name='球衣號碼')
    positions = models.CharField(max_length=100, verbose_name='位置', help_text='可選擇多個位置，以逗號分隔')
    height = models.FloatField(blank=True, null=True, verbose_name='身高(cm)')
    weight = models.FloatField(blank=True, null=True, verbose_name='體重(kg)')
    age = models.IntegerField(verbose_name='年齡')
    stamina = models.CharField(max_length=10, choices=ABILITY_CHOICES, verbose_name='體力')
    speed = models.CharField(max_length=10, choices=ABILITY_CHOICES, verbose_name='速度')
    technique = models.CharField(max_length=10, choices=ABILITY_CHOICES, verbose_name='技術')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    
    class Meta:
        verbose_name = '球員'
        verbose_name_plural = '球員'
        unique_together = ['team', 'jersey_number']
    
    def __str__(self):
        return f"{self.nickname} - {self.team.name}"
    
    def get_positions_list(self):
        """返回位置列表"""
        if self.positions:
            return [pos.strip() for pos in self.positions.split(',')]
        return []
    
    def set_positions_list(self, positions_list):
        """設置位置列表"""
        self.positions = ','.join(positions_list)

class League(models.Model):
    name = models.CharField(max_length=100, verbose_name='聯賽名稱')
    season = models.CharField(max_length=20, verbose_name='賽季')
    group = models.CharField(
        max_length=50,
        choices=[
            ('幼兒組', '幼兒組'),
            ('國小組', '國小組'),
            ('國中組', '國中組'),
            ('高中組', '高中組'),
            ('成人組', '成人組'),
        ],
        verbose_name='組別'
    )
    start_date = models.DateField(verbose_name='開始日期')
    end_date = models.DateField(verbose_name='結束日期')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    coach = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'coach'},
        verbose_name='負責教練'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    
    class Meta:
        verbose_name = '聯賽'
        verbose_name_plural = '聯賽'
    
    def __str__(self):
        return f"{self.name} - {self.season} ({self.group})"

class Match(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, verbose_name='聯賽')
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        verbose_name='我方球隊'
    )
    opponent_name = models.CharField(max_length=100, verbose_name='對手名稱')
    match_date = models.DateTimeField(verbose_name='比賽時間')
    venue = models.CharField(max_length=200, verbose_name='比賽場地')
    our_score = models.IntegerField(blank=True, null=True, verbose_name='我方得分')
    opponent_score = models.IntegerField(blank=True, null=True, verbose_name='對手得分')
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', '已安排'),
            ('in_progress', '確認中'),
            ('finished', '已結束'),
            ('cancelled', '已取消'),
            ('postponed', '已延期'),
        ],
        default='scheduled',
        verbose_name='比賽狀態'
    )
    notes = models.TextField(blank=True, null=True, verbose_name='備註')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    
    class Meta:
        verbose_name = '比賽'
        verbose_name_plural = '比賽'
    
    def __str__(self):
        return f"{self.team.name} vs {self.opponent_name} - {self.match_date.strftime('%Y-%m-%d %H:%M')}"

class PlayerStats(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name='球員')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, verbose_name='比賽')
    goals = models.IntegerField(default=0, verbose_name='進球數')
    assists = models.IntegerField(default=0, verbose_name='助攻數')
    yellow_cards = models.IntegerField(default=0, verbose_name='黃牌數')
    red_cards = models.IntegerField(default=0, verbose_name='紅牌數')
    minutes_played = models.IntegerField(default=0, verbose_name='出場時間(分鐘)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    
    class Meta:
        verbose_name = '球員統計'
        verbose_name_plural = '球員統計'
        unique_together = ['player', 'match']
    
    def __str__(self):
        return f"{self.player.nickname} - {self.match}"

class PlayerMatchParticipation(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name='球員')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, verbose_name='比賽')
    is_participating = models.BooleanField(default=True, verbose_name='是否參加')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    
    class Meta:
        verbose_name = '球員參加比賽'
        verbose_name_plural = '球員參加比賽'
        unique_together = ['player', 'match']
    
    def __str__(self):
        participation_status = "參加" if self.is_participating else "不參加"
        return f"{self.player.nickname} - {self.match} ({participation_status})"

