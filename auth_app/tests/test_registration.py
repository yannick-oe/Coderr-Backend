"""Tests for the registration endpoint."""

from unittest import mock

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from auth_app.models import ProfileType

REGISTRATION_URL = "/api/registration/"
RESPONSE_KEYS = {"token", "username", "email", "user_id"}
ORDERED_KEYS = ["token", "username", "email", "user_id"]


def payload(**overrides):
    """Return a valid registration payload with optional overrides."""
    data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "SecurePass123",
        "repeated_password": "SecurePass123",
        "type": ProfileType.CUSTOMER,
    }
    data.update(overrides)
    return data


class RegistrationSuccessTests(APITestCase):
    """Happy-path registration for both account types."""

    def test_customer_registration_returns_201_and_keys(self):
        """A valid customer registration returns 201 and exact keys."""
        response = self.client.post(REGISTRATION_URL, payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data), RESPONSE_KEYS)

    def test_response_key_order_matches_contract(self):
        """Response keys appear in the documented order."""
        response = self.client.post(REGISTRATION_URL, payload(), format="json")
        self.assertEqual(list(response.data), ORDERED_KEYS)

    def test_customer_profile_and_token_created(self):
        """Registration creates the profile and a matching token."""
        self.client.post(REGISTRATION_URL, payload(), format="json")
        user = User.objects.get(username="newuser")
        self.assertEqual(user.profile.type, ProfileType.CUSTOMER)
        self.assertTrue(Token.objects.filter(user=user).exists())

    def test_business_registration_sets_business_type(self):
        """A business registration stores the business profile type."""
        data = payload(type=ProfileType.BUSINESS)
        response = self.client.post(REGISTRATION_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="newuser")
        self.assertEqual(user.profile.type, ProfileType.BUSINESS)

    def test_write_only_password_fields_absent_from_response(self):
        """The write-only password fields never appear in output."""
        response = self.client.post(REGISTRATION_URL, payload(), format="json")
        self.assertNotIn("password", response.data)
        self.assertNotIn("repeated_password", response.data)


class RegistrationValidationTests(APITestCase):
    """Registration rejects invalid or conflicting data with 400."""

    def test_password_mismatch_rejected(self):
        """Mismatched passwords return 400."""
        data = payload(repeated_password="different")
        response = self.client.post(REGISTRATION_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_username_rejected(self):
        """A duplicate username returns 400."""
        User.objects.create_user(username="newuser", password="x")
        response = self.client.post(REGISTRATION_URL, payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_email_rejected(self):
        """A duplicate email returns 400."""
        User.objects.create_user(
            username="other", email="new@example.com", password="x"
        )
        response = self.client.post(REGISTRATION_URL, payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_field_rejected(self):
        """A missing required field returns 400."""
        data = payload()
        del data["email"]
        response = self.client.post(REGISTRATION_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_type_rejected(self):
        """An unknown account type returns 400."""
        data = payload(type="admin")
        response = self.client.post(REGISTRATION_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_user_created_on_invalid_data(self):
        """A rejected registration must not create a user."""
        data = payload(type="admin")
        self.client.post(REGISTRATION_URL, data, format="json")
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_atomic_rollback_on_token_failure(self):
        """A failure creating the token rolls back user and profile."""
        target = "auth_app.api.serializers.Token.objects.create"
        with mock.patch(target, side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                self.client.post(REGISTRATION_URL, payload(), format="json")
        self.assertFalse(User.objects.filter(username="newuser").exists())
