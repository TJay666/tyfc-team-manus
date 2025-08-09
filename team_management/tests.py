from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Team, League, Player, Match, PlayerMatchParticipation, PlayerStats
from datetime import date, datetime, timedelta
from django.utils import timezone

User = get_user_model()


class TeamManagementTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username="admin1", password="adminpass", user_type="admin", is_approved=True
		)
		self.coach = User.objects.create_user(
			username="coach1", password="coachpass", user_type="coach", is_approved=True
		)
		self.player_user = User.objects.create_user(
			username="playeruser", password="playerpass", user_type="player", is_approved=True
		)

	def test_coach_can_create_team(self):
		self.client.login(username="coach1", password="coachpass")
		resp = self.client.post(
			reverse("team_create"),
			{
				"name": "Falcons A",
				"group": "成人組",
				"description": "Test team",
			},
			follow=True,
		)
		self.assertEqual(resp.status_code, 200)
		self.assertTrue(Team.objects.filter(name="Falcons A").exists())
		team = Team.objects.get(name="Falcons A")
		self.assertEqual(team.coach, self.coach)

	def test_player_cannot_access_team_create(self):
		self.client.login(username="playeruser", password="playerpass")
		resp = self.client.get(reverse("team_create"))
		# 應該被重定向（無權限）
		self.assertEqual(resp.status_code, 302)
		self.assertIn("/dashboard/", resp["Location"])

	def test_admin_can_assign_coach_when_creating_team(self):
		self.client.login(username="admin1", password="adminpass")
		resp = self.client.post(
			reverse("team_create"),
			{
				"name": "Falcons B",
				"group": "高中組",
				"description": "Admin created",
				"coach": self.coach.id,
			},
			follow=True,
		)
		self.assertEqual(resp.status_code, 200)
		team = Team.objects.get(name="Falcons B")
		self.assertEqual(team.coach, self.coach)

	def test_league_creation_by_coach(self):
		self.client.login(username="coach1", password="coachpass")
		resp = self.client.post(
			reverse("league_create"),
			{
				"name": "Summer League",
				"season": "2025",
				"group": "成人組",
				"start_date": date.today().strftime("%Y-%m-%d"),
				"end_date": date.today().strftime("%Y-%m-%d"),
				"description": "Summer test",
			},
			follow=True,
		)
		self.assertEqual(resp.status_code, 200)
		self.assertTrue(League.objects.filter(name="Summer League").exists())
		league = League.objects.get(name="Summer League")
		self.assertEqual(league.coach, self.coach)

	def test_player_cannot_create_league(self):
		self.client.login(username="playeruser", password="playerpass")
		resp = self.client.get(reverse("league_create"))
		self.assertEqual(resp.status_code, 302)
		self.assertIn("/dashboard/", resp["Location"])


class MatchAndParticipationTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.admin = User.objects.create_user(
			username="adminx", password="adminpass", user_type="admin", is_approved=True
		)
		self.coach = User.objects.create_user(
			username="coachx", password="coachpass", user_type="coach", is_approved=True
		)
		self.player_user = User.objects.create_user(
			username="playerx", password="playerpass", user_type="player", is_approved=True
		)
		# 建立球隊與聯賽
		self.team = Team.objects.create(name="Alpha", coach=self.coach, group="成人組")
		today = date.today().strftime("%Y-%m-%d")
		self.league = League.objects.create(
			name="League1",
			season="2025",
			group="成人組",
			start_date=today,
			end_date=today,
			coach=self.coach,
		)
		# 建立 Player profile
		self.player = Player.objects.create(
			user=self.player_user,
			nickname="PX",
			team=self.team,
			jersey_number=9,
			positions="FW",
			height=180,
			weight=70,
			age=20,
			stamina="優",
			speed="優",
			technique="優",
		)

	def test_coach_create_match_and_auto_participation_records(self):
		self.client.login(username="coachx", password="coachpass")
		match_datetime = (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
		resp = self.client.post(
			reverse("match_create"),
			{
				"league": self.league.id,
				"team": self.team.id,
				"opponent_name": "Rivals",
				"match_date": match_datetime,
				"venue": "Stadium A",
				"status": "scheduled",
			},
			follow=True,
		)
		self.assertEqual(resp.status_code, 200)
		match = Match.objects.get(opponent_name="Rivals")
		# 自動建立參與紀錄
		self.assertTrue(
			PlayerMatchParticipation.objects.filter(match=match, player=self.player, is_participating=True).exists()
		)

	def test_player_toggle_participation(self):
		# 先建立一場比賽
		match = Match.objects.create(
			league=self.league,
			team=self.team,
			opponent_name="Temp",
			match_date=timezone.now() + timedelta(days=1),
			venue="Field",
			status="scheduled",
		)
		PlayerMatchParticipation.objects.create(player=self.player, match=match, is_participating=True)
		self.client.login(username="playerx", password="playerpass")
		resp = self.client.post(
			reverse("match_participate", args=[match.id]), {"is_participating": "false"}, follow=True
		)
		self.assertEqual(resp.status_code, 200)
		self.assertFalse(PlayerMatchParticipation.objects.get(player=self.player, match=match).is_participating)

	def test_coach_update_player_stats_in_participants_view(self):
		match = Match.objects.create(
			league=self.league,
			team=self.team,
			opponent_name="StatsClub",
			match_date=timezone.now() + timedelta(days=1),
			venue="Arena",
			status="scheduled",
		)
		PlayerMatchParticipation.objects.create(player=self.player, match=match, is_participating=True)
		self.client.login(username="coachx", password="coachpass")
		# mimic form field naming: player_<id>_<field>
		resp = self.client.post(
			reverse("match_participants", args=[match.id]),
			{f"player_{self.player.id}_goals": "2", f"player_{self.player.id}_assists": "1"},
			follow=True,
		)
		self.assertEqual(resp.status_code, 200)
		stats = PlayerStats.objects.get(player=self.player, match=match)
		self.assertEqual(stats.goals, 2)
		self.assertEqual(stats.assists, 1)

	def test_player_cannot_access_matches_list(self):
		self.client.login(username="playerx", password="playerpass")
		resp = self.client.get(reverse("matches"))
		self.assertEqual(resp.status_code, 302)
		self.assertIn("/dashboard/", resp["Location"])


class DashboardVisibilityTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.admin = User.objects.create_user(
			username="admindb", password="adminpass", user_type="admin", is_approved=True
		)
		self.coach = User.objects.create_user(
			username="coachdb", password="coachpass", user_type="coach", is_approved=True
		)
		self.player_user = User.objects.create_user(
			username="playerdb", password="playerpass", user_type="player", is_approved=True
		)
		self.team = Team.objects.create(name="DashTeam", coach=self.coach, group="成人組")
		self.player = Player.objects.create(
			user=self.player_user,
			nickname="DashP",
			team=self.team,
			jersey_number=10,
			positions="FW",
			age=18,
			stamina="優",
			speed="優",
			technique="優",
		)

	def test_admin_dashboard_contains_total_users(self):
		self.client.login(username="admindb", password="adminpass")
		resp = self.client.get(reverse("dashboard"))
		self.assertEqual(resp.status_code, 200)
		# 檢查模板中顯示的中文標籤 "總使用者數"
		self.assertContains(resp, "總使用者數")

	def test_coach_dashboard_shows_my_teams(self):
		self.client.login(username="coachdb", password="coachpass")
		resp = self.client.get(reverse("dashboard"))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "DashTeam")

	def test_player_dashboard_shows_recent_matches_section_even_if_empty(self):
		self.client.login(username="playerdb", password="playerpass")
		resp = self.client.get(reverse("dashboard"))
		self.assertEqual(resp.status_code, 200)
		# 檢查球員儀表板的中文區塊標題
		self.assertContains(resp, "我的球隊資訊")


class PlayerStatsCrudTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.admin = User.objects.create_user(
			username="adminstats", password="adminpass", user_type="admin", is_approved=True
		)
		self.coach = User.objects.create_user(
			username="coachstats", password="coachpass", user_type="coach", is_approved=True
		)
		self.other_coach = User.objects.create_user(
			username="coachother", password="coachpass", user_type="coach", is_approved=True
		)
		self.player_user = User.objects.create_user(
			username="playerstats", password="playerpass", user_type="player", is_approved=True
		)
		self.team = Team.objects.create(name="StatsTeam", coach=self.coach, group="成人組")
		self.league = League.objects.create(
			name="StatsLeague",
			season="2025",
			group="成人組",
			start_date=date.today(),
			end_date=date.today(),
			coach=self.coach,
		)
		self.match = Match.objects.create(
			league=self.league,
			team=self.team,
			opponent_name="Opp",
			match_date=timezone.now() + timedelta(days=1),
			venue="Arena",
			status="scheduled",
		)
		self.player = Player.objects.create(
			user=self.player_user,
			nickname="StatP",
			team=self.team,
			jersey_number=11,
			positions="FW",
			age=19,
			stamina="優",
			speed="優",
			technique="優",
		)

	def test_coach_create_player_stats(self):
		self.client.login(username="coachstats", password="coachpass")
		resp = self.client.post(
			reverse("player_stats_create"),
			{
				"player": self.player.id,
				"match": self.match.id,
				"goals": 1,
				"assists": 2,
				"minutes_played": 30,
			},
			follow=True,
		)
		self.assertEqual(resp.status_code, 200)
		self.assertTrue(PlayerStats.objects.filter(player=self.player, match=self.match, goals=1).exists())

	def test_other_coach_cannot_create_stats_for_not_owned_team(self):
		self.client.login(username="coachother", password="coachpass")
		resp = self.client.post(
			reverse("player_stats_create"),
			{
				"player": self.player.id,
				"match": self.match.id,
				"goals": 1,
			},
			follow=True,
		)
		# 會被 redirect（拒絕）
		self.assertEqual(resp.status_code, 200)
		# 不應建立資料
		self.assertFalse(PlayerStats.objects.filter(player=self.player, match=self.match).exists())

	def test_admin_edit_player_stats(self):
		stats = PlayerStats.objects.create(player=self.player, match=self.match, goals=0, assists=0, minutes_played=0)
		self.client.login(username="adminstats", password="adminpass")
		resp = self.client.post(
			reverse("player_stats_edit", args=[stats.id]),
			{
				"player": self.player.id,
				"match": self.match.id,
				"goals": 3,
				"assists": 1,
				"minutes_played": 60,
			},
			follow=True,
		)
		self.assertEqual(resp.status_code, 200)
		stats.refresh_from_db()
		self.assertEqual(stats.goals, 3)
		self.assertEqual(stats.assists, 1)

	def test_delete_player_stats(self):
		stats = PlayerStats.objects.create(player=self.player, match=self.match, goals=2, assists=0, minutes_played=10)
		self.client.login(username="adminstats", password="adminpass")
		resp = self.client.post(reverse("player_stats_delete", args=[stats.id]), follow=True)
		self.assertEqual(resp.status_code, 200)
		self.assertFalse(PlayerStats.objects.filter(id=stats.id).exists())


class MatchEditDeletePermissionTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username="adminperm", password="adminpass", user_type="admin", is_approved=True
		)
		self.coach1 = User.objects.create_user(
			username="coachperm1", password="coachpass", user_type="coach", is_approved=True
		)
		self.coach2 = User.objects.create_user(
			username="coachperm2", password="coachpass", user_type="coach", is_approved=True
		)
		self.player_user = User.objects.create_user(
			username="playerperm", password="playerpass", user_type="player", is_approved=True
		)
		self.team1 = Team.objects.create(name="PermTeam1", coach=self.coach1, group="成人組")
		self.team2 = Team.objects.create(name="PermTeam2", coach=self.coach2, group="成人組")
		self.league1 = League.objects.create(
			name="PermLeague1",
			season="2025",
			group="成人組",
			start_date=date.today(),
			end_date=date.today(),
			coach=self.coach1,
		)
		self.league2 = League.objects.create(
			name="PermLeague2",
			season="2025",
			group="成人組",
			start_date=date.today(),
			end_date=date.today(),
			coach=self.coach2,
		)
		self.match1 = Match.objects.create(
			league=self.league1,
			team=self.team1,
			opponent_name="Opp1",
			match_date=timezone.now() + timedelta(days=1),
			venue="A",
			status="scheduled",
		)
		self.match2 = Match.objects.create(
			league=self.league2,
			team=self.team2,
			opponent_name="Opp2",
			match_date=timezone.now() + timedelta(days=1),
			venue="B",
			status="scheduled",
		)

	def test_coach_can_edit_own_match(self):
		self.client.login(username="coachperm1", password="coachpass")
		resp = self.client.post(
			reverse("match_edit", args=[self.match1.id]),
			{
				"league": self.league1.id,
				"team": self.team1.id,
				"opponent_name": "Opp1Updated",
				"match_date": (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M"),
				"venue": "A1",
				"status": "scheduled",
			},
			follow=True,
		)
		self.assertEqual(resp.status_code, 200)
		self.match1.refresh_from_db()
		self.assertEqual(self.match1.opponent_name, "Opp1Updated")

	def test_coach_cannot_edit_other_match(self):
		self.client.login(username="coachperm1", password="coachpass")
		resp = self.client.post(
			reverse("match_edit", args=[self.match2.id]),
			{
				"league": self.league2.id,
				"team": self.team2.id,
				"opponent_name": "ShouldNot",
				"match_date": (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M"),
				"venue": "B1",
				"status": "scheduled",
			},
			follow=True,
		)
		self.assertEqual(resp.status_code, 200)
		self.match2.refresh_from_db()
		self.assertEqual(self.match2.opponent_name, "Opp2")  # unchanged

	def test_player_cannot_edit_match(self):
		self.client.login(username="playerperm", password="playerpass")
		resp = self.client.get(reverse("match_edit", args=[self.match1.id]))
		self.assertEqual(resp.status_code, 302)
		self.assertIn("/dashboard/", resp["Location"])

	def test_admin_can_delete_match(self):
		self.client.login(username="adminperm", password="adminpass")
		resp = self.client.post(reverse("match_delete", args=[self.match1.id]), follow=True)
		self.assertEqual(resp.status_code, 200)
		self.assertFalse(Match.objects.filter(id=self.match1.id).exists())

	def test_coach_cannot_delete_other_match(self):
		self.client.login(username="coachperm1", password="coachpass")
		resp = self.client.post(reverse("match_delete", args=[self.match2.id]), follow=True)
		self.assertEqual(resp.status_code, 200)
		self.assertTrue(Match.objects.filter(id=self.match2.id).exists())


class StatisticsViewTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username="adminstatsview", password="adminpass", user_type="admin", is_approved=True
		)
		self.coach = User.objects.create_user(
			username="coachstatsview", password="coachpass", user_type="coach", is_approved=True
		)
		self.player_user = User.objects.create_user(
			username="playerstatsview", password="playerpass", user_type="player", is_approved=True
		)
		self.team = Team.objects.create(name="StatViewTeam", coach=self.coach, group="成人組")
		self.league = League.objects.create(
			name="StatViewLeague",
			season="2025",
			group="成人組",
			start_date=date.today(),
			end_date=date.today(),
			coach=self.coach,
		)
		# finished 與 scheduled 各一場
		self.match_finished = Match.objects.create(
			league=self.league,
			team=self.team,
			opponent_name="FinishedOpp",
			match_date=timezone.now() - timedelta(days=1),
			venue="SV A",
			status="finished",
			our_score=2,
			opponent_score=1,
		)
		self.match_scheduled = Match.objects.create(
			league=self.league,
			team=self.team,
			opponent_name="SchedOpp",
			match_date=timezone.now() + timedelta(days=1),
			venue="SV B",
			status="scheduled",
		)
		self.player = Player.objects.create(
			user=self.player_user,
			nickname="SVP",
			team=self.team,
			jersey_number=7,
			positions="FW",
			age=17,
			stamina="優",
			speed="優",
			technique="優",
		)
		# Player participation + stats for finished match
		PlayerMatchParticipation.objects.create(player=self.player, match=self.match_finished, is_participating=True)
		PlayerMatchParticipation.objects.create(player=self.player, match=self.match_scheduled, is_participating=True)
		PlayerStats.objects.create(player=self.player, match=self.match_finished, goals=1, assists=0, minutes_played=90)

	def test_admin_statistics_counts(self):
		self.client.login(username="adminstatsview", password="adminpass")
		resp = self.client.get(reverse("statistics"))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "finished")  # status mapping labels may appear
		# finished_matches = 1
		self.assertIn("finished_matches", resp.context)
		self.assertEqual(resp.context["finished_matches"], 1)

	def test_coach_statistics_my_counts(self):
		self.client.login(username="coachstatsview", password="coachpass")
		resp = self.client.get(reverse("statistics"))
		self.assertEqual(resp.status_code, 200)
		self.assertIn("my_teams_count", resp.context)
		self.assertEqual(resp.context["my_teams_count"], 1)
		self.assertEqual(resp.context["my_matches_count"], 2)

	def test_player_statistics_personal_totals(self):
		self.client.login(username="playerstatsview", password="playerpass")
		resp = self.client.get(reverse("statistics"))
		self.assertEqual(resp.status_code, 200)
		self.assertIn("player_stats", resp.context)
		self.assertEqual(resp.context["player_stats"]["matches_played"], 1)  # only finished matches counted
		self.assertEqual(resp.context["player_stats"]["total_goals"], 1)


class HealthCheckTests(TestCase):
	def test_healthz(self):
		resp = self.client.get('/healthz')
		self.assertEqual(resp.status_code, 200)
		self.assertJSONEqual(
			resp.content.decode(),
			{ 'status': 'ok', 'db': 'ok', 'app': 'tyfc-team-manus', 'elapsed_ms': resp.json()['elapsed_ms'] }
		)

