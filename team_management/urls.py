from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Teams URLs
    path('teams/', views.teams, name='teams'),
    path('teams/create/', views.team_create, name='team_create'),
    path('teams/<int:team_id>/edit/', views.team_edit, name='team_edit'),
    path('teams/<int:team_id>/delete/', views.team_delete, name='team_delete'),
    
    # Players URLs
    path('players/', views.players, name='players'),
    path('players/create/', views.player_create, name='player_create'),
    path('players/<int:player_id>/edit/', views.player_edit, name='player_edit'),
    path('players/<int:player_id>/delete/', views.player_delete, name='player_delete'),
    
    # Matches URLs
    path('matches/', views.matches, name='matches'),
    path('matches/create/', views.match_create, name='match_create'),
    path('matches/<int:match_id>/edit/', views.match_edit, name='match_edit'),
    path('matches/<int:match_id>/delete/', views.match_delete, name='match_delete'),
    path('matches/<int:match_id>/participants/', views.match_participants, name='match_participants'),
    
    # Player Matches URLs
    path('my-matches/', views.my_matches, name='my_matches'),
    path('my-matches/<int:match_id>/participate/', views.match_participate, name='match_participate'),
    
    # Leagues URLs
    path('leagues/', views.leagues, name='leagues'),
    path('leagues/create/', views.league_create, name='league_create'),
    path('leagues/<int:league_id>/edit/', views.league_edit, name='league_edit'),
    path('leagues/<int:league_id>/delete/', views.league_delete, name='league_delete'),
    
    # Statistics
    path('statistics/', views.statistics, name='statistics'),
]

