from django.contrib import admin
from .models import Team, Player, League, Match, PlayerStats, PlayerMatchParticipation

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'coach', 'group', 'created_at']
    list_filter = ['group', 'created_at']
    search_fields = ['name', 'coach__username']

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['nickname', 'user', 'team', 'jersey_number', 'positions', 'age']
    list_filter = ['team', 'stamina', 'speed', 'technique']
    search_fields = ['nickname', 'user__username', 'team__name']

@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ['name', 'season', 'group', 'start_date', 'end_date']
    list_filter = ['group', 'season']
    search_fields = ['name', 'season']

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ["league", "match_date", "status", "opponent_name", "score"]
    list_filter = ["status", "league", "match_date"]
    search_fields = ["team__name", "opponent_name"]

    def score(self, obj):
        if obj.our_score is not None and obj.opponent_score is not None:
            return f"{obj.our_score} - {obj.opponent_score}"
        return "N/A"
    score.short_description = "比分"

@admin.register(PlayerStats)
class PlayerStatsAdmin(admin.ModelAdmin):
    list_display = ["player", "match", "goals", "assists", "yellow_cards", "red_cards"]
    list_filter = ["match__league", "match__match_date"]
    search_fields = ["player__nickname", "match__team__name", "match__opponent_name"]

@admin.register(PlayerMatchParticipation)
class PlayerMatchParticipationAdmin(admin.ModelAdmin):
    list_display = ["player", "match", "is_participating", "updated_at"]
    list_filter = ["is_participating", "match__league", "match__match_date"]
    search_fields = ["player__nickname", "match__team__name", "match__opponent_name"]

