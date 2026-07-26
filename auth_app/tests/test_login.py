"""Tests for the login endpoint."""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

LOGIN_URL = "/api/login/"
RESPONSE_KEYS = {"token", "username", "email", "user_id"}
ORDERED_KEYS = ["token", "username", "email", "user_id"]
UNKNOWN_TOKEN = "Token " + "a" * 40
MALFORMED_HEADER = "Token malformed value"
AUTH_HEADER_CASES = [
    ("none", None),
    ("unknown_token", UNKNOWN_TOKEN),
    ("malformed", MALFORMED_HEADER),
]


class LoginTests(APITestCase):
    """Token login with username and password."""

    def setUp(self):
        """Create a user with a known password and existing token."""
        self.user = User.objects.create_user(
            username="andrey",
            email="andrey@example.com",
            password="asdasd",
        )
        self.token = Token.objects.create(user=self.user)

    def login(self, username, password):
        """Post credentials to the login endpoint."""
        body = {"username": username, "password": password}
        return self.client.post(LOGIN_URL, body, format="json")

    def test_login_success_returns_200_and_keys(self):
        """Valid credentials return 200 and the exact key set."""
        response = self.login("andrey", "asdasd")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), RESPONSE_KEYS)

    def test_login_response_key_order_matches_contract(self):
        """Response keys appear in the documented order."""
        response = self.login("andrey", "asdasd")
        self.assertEqual(list(response.data), ORDERED_KEYS)

    def test_login_reuses_existing_token(self):
        """Login returns the user's existing token, not a new one."""
        response = self.login("andrey", "asdasd")
        self.assertEqual(response.data["token"], self.token.key)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)

    def test_login_wrong_password_returns_400(self):
        """A wrong password returns 400, not 401."""
        response = self.login("andrey", "wrongpass")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_unknown_username_returns_400(self):
        """An unknown username returns 400."""
        response = self.login("ghost", "asdasd")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginIgnoresAuthHeaderTests(APITestCase):
    """Login succeeds regardless of any Authorization header."""

    def setUp(self):
        """Create a user with known credentials."""
        User.objects.create_user(username="andrey", password="asdasd")

    def login(self, header):
        """Post valid credentials under the given auth header."""
        if header is None:
            self.client.credentials()
        else:
            self.client.credentials(HTTP_AUTHORIZATION=header)
        body = {"username": "andrey", "password": "asdasd"}
        return self.client.post(LOGIN_URL, body, format="json")

    def test_returns_200_for_every_header_variant(self):
        """Valid credentials return 200 with no, unknown, or bad header."""
        for label, header in AUTH_HEADER_CASES:
            with self.subTest(header=label):
                response = self.login(header)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
