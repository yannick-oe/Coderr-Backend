"""Tests for the profile update (PATCH) endpoint."""

import shutil
import tempfile

from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from auth_app.tests.utils import authenticate, create_profile, make_image

TEMP_MEDIA = tempfile.mkdtemp()

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


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProfilePatchTests(APITestCase):
    """PATCH /api/profile/{pk}/ ownership and updates."""

    def setUp(self):
        """Create an owner profile and another user."""
        self.profile = create_profile(
            "owner",
            ProfileType.BUSINESS,
            user_kwargs={"email": "owner@ex.de", "first_name": "Ann"},
        )
        self.other = User.objects.create_user(username="intruder")

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary media directory."""
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def test_owner_patch_json_updates_both_models(self):
        """A JSON PATCH updates the User and profile rows."""
        authenticate(self.client, self.profile.user)
        body = {"first_name": "Bob", "location": "Kiel"}
        response = self.client.patch(
            detail_url(self.profile.pk), body, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.user.first_name, "Bob")
        self.assertEqual(self.profile.location, "Kiel")

    def test_patch_response_shape_and_order(self):
        """The PATCH response matches the detail key order."""
        authenticate(self.client, self.profile.user)
        response = self.client.patch(
            detail_url(self.profile.pk), {"tel": "123"}, format="json"
        )
        self.assertEqual(list(response.data), DETAIL_KEYS)

    def test_owner_patch_multipart_with_file(self):
        """A multipart PATCH stores the file and returns a URL."""
        authenticate(self.client, self.profile.user)
        body = {"location": "Ulm", "file": make_image()}
        response = self.client.patch(
            detail_url(self.profile.pk), body, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["file"].startswith("http"))

    def test_patch_other_user_returns_403(self):
        """A non-owner PATCH returns 403."""
        authenticate(self.client, self.other)
        response = self.client.patch(
            detail_url(self.profile.pk), {"tel": "1"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_unauthenticated_returns_401(self):
        """An unauthenticated PATCH returns 401."""
        response = self.client.patch(
            detail_url(self.profile.pk), {"tel": "1"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_readonly_field_is_ignored(self):
        """A read-only field in the payload is ignored, not rejected."""
        authenticate(self.client, self.profile.user)
        body = {"type": ProfileType.CUSTOMER}
        response = self.client.patch(
            detail_url(self.profile.pk), body, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.type, ProfileType.BUSINESS)
