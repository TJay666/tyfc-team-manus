from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthenticationFlowTests(TestCase):
	def setUp(self):
		# 建立一個管理員與一個教練及一個球員（尚未核准）
		self.admin = User.objects.create_user(
			username="admin1", password="adminpass", user_type="admin", is_approved=True
		)
		self.coach = User.objects.create_user(
			username="coach1", password="coachpass", user_type="coach", is_approved=True
		)
		self.player_pending = User.objects.create_user(
			username="player1", password="playerpass", user_type="player", is_approved=False
		)

	def test_unapproved_user_cannot_login(self):
		resp = self.client.post(
			reverse("login"), {"username": "player1", "password": "playerpass"}, follow=True
		)
		# 應該仍停留在登入頁（狀態 200）
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "尚未通過審核", status_code=200)

	def test_approved_user_can_login_and_redirect_dashboard(self):
		resp = self.client.post(
			reverse("login"), {"username": "coach1", "password": "coachpass"}
		)
		self.assertEqual(resp.status_code, 302)
		self.assertIn("/dashboard/", resp["Location"])  # redirect to dashboard

	def test_admin_can_view_user_management(self):
		self.client.login(username="admin1", password="adminpass")
		resp = self.client.get(reverse("user_management"))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, "使用者")

	def test_non_admin_cannot_view_user_management(self):
		self.client.login(username="coach1", password="coachpass")
		resp = self.client.get(reverse("user_management"))
		# 會被轉向 dashboard
		self.assertEqual(resp.status_code, 302)
		self.assertIn("/dashboard/", resp["Location"])

