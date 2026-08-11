from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse("auth-register")
        self.login_url = reverse("auth-login")
        self.me_url = reverse("auth-me")
        self.refresh_url = reverse("auth-token-refresh")
        self.logout_url = reverse("auth-logout")
        self.change_password_url = reverse("auth-change-password")
        self.forgot_url = reverse("auth-forgot-password")
        self.reset_url = reverse("auth-reset-password")

        self.user = User.objects.create_user(
            email="staff@example.com",
            password="StrongPass123!",
            first_name="Staff",
            last_name="User",
            phone="9999999999",
        )

    def test_register_creates_viewer_and_returns_tokens(self):
        payload = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "phone": "8888888888",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["user"]["role"], "viewer")
        self.assertIn("access", response.data["data"]["tokens"])
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_login_returns_jwt_and_user(self):
        response = self.client.post(
            self.login_url,
            {"email": "staff@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["user"]["email"], "staff@example.com")
        self.assertIn("access", response.data["data"]["tokens"])

    def test_me_requires_auth_and_returns_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], "staff@example.com")

    def test_update_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            self.me_url,
            {"first_name": "Updated", "phone": "7777777777"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.phone, "7777777777")

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.change_password_url,
            {
                "current_password": "StrongPass123!",
                "new_password": "EvenStronger123!",
                "new_password_confirm": "EvenStronger123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("EvenStronger123!"))

    def test_forgot_and_reset_password_flow(self):
        from django.core import mail
        import re

        forgot = self.client.post(
            self.forgot_url, {"email": "staff@example.com"}, format="json"
        )
        self.assertEqual(forgot.status_code, status.HTTP_200_OK)
        self.assertTrue(forgot.data["success"])
        self.assertEqual(len(mail.outbox), 1)

        match = re.search(r"uid=([^&\s]+)&token=([^\s]+)", mail.outbox[0].body)
        self.assertIsNotNone(match)
        uid, token = match.group(1), match.group(2)

        reset = self.client.post(
            self.reset_url,
            {
                "uid": uid,
                "token": token,
                "new_password": "ResetPass123!",
                "new_password_confirm": "ResetPass123!",
            },
            format="json",
        )
        self.assertEqual(reset.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("ResetPass123!"))

    def test_logout_blacklists_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        logout = self.client.post(
            self.logout_url, {"refresh": str(refresh)}, format="json"
        )
        self.assertEqual(logout.status_code, status.HTTP_200_OK)

        # Refresh should fail after blacklist
        refresh_response = self.client.post(
            self.refresh_url, {"refresh": str(refresh)}, format="json"
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
