"""Tests for the profile detail (GET) endpoint."""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from auth_app.tests.utils import authenticate, create_profile

DETAIL_KEYS = [
    "user",
    "username",
    "first_name",
    "last_name",
    "file",
    "location",
    "tel",
    "description",
    "working_hours",
    "type",
    "email",
    "created_at",
]


def detail_url(pk):
    """Return the profile detail path for a user id."""
    return f"/api/profile/{pk}/"


class ProfileDetailTests(APITestCase):
    """GET /api/profile/{pk}/ access and response shape."""

    def setUp(self):
        """Create an owner profile and a second user."""
        self.profile = create_profile(
            "owner",
            ProfileType.BUSINESS,
            user_kwargs={"email": "owner@ex.de", "first_name": "Ann"},
            location="Berlin",
        )
        self.other = User.objects.create_user(username="other")

    def test_owner_can_read_profile(self):
        """The owner reads their profile with 200 and exact keys."""
        authenticate(self.client, self.profile.user)
        response = self.client.get(detail_url(self.profile.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), DETAIL_KEYS)

    def test_other_user_can_read_profile(self):
        """Any authenticated user may read any profile."""
        authenticate(self.client, self.other)
        response = self.client.get(detail_url(self.profile.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_read_returns_401(self):
        """An unauthenticated read returns 401."""
        response = self.client.get(detail_url(self.profile.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_pk_returns_404(self):
        """A pk with no profile returns 404."""
        authenticate(self.client, self.other)
        response = self.client.get(detail_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_field_is_integer_id(self):
        """The user field is the integer user id."""
        authenticate(self.client, self.profile.user)
        response = self.client.get(detail_url(self.profile.pk))
        self.assertEqual(response.data["user"], self.profile.pk)

    def test_blank_values_serialize_as_empty_strings(self):
        """Missing values serialize as empty strings, never null."""
        authenticate(self.client, self.other)
        response = self.client.get(detail_url(self.profile.pk))
        for field in ("last_name", "tel", "description", "working_hours"):
            self.assertEqual(response.data[field], "")
        self.assertEqual(response.data["file"], "")
