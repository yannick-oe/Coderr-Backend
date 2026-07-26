"""Tests for auth_app model string representations."""

from django.test import TestCase

from auth_app.models import ProfileType
from auth_app.tests.utils import create_profile


class UserProfileStrTests(TestCase):
    """The UserProfile __str__ shown in the admin changelist."""

    def test_str_shows_username_and_type(self):
        """__str__ is 'username (type)'."""
        profile = create_profile("bob", ProfileType.BUSINESS)
        profile.refresh_from_db()
        self.assertEqual(str(profile), "bob (business)")
