"""Tests for offers_app model string representations."""

from django.test import TestCase

from auth_app.models import ProfileType
from offers_app.tests.utils import create_offer, make_user


class OfferStrTests(TestCase):
    """The Offer and OfferDetail __str__ shown in the admin."""

    def setUp(self):
        """Create a business user and an offer with details."""
        self.user = make_user("biz", ProfileType.BUSINESS)
        self.offer = create_offer(self.user)

    def test_offer_str_is_title(self):
        """Offer __str__ is its title."""
        self.assertEqual(str(self.offer), "T")

    def test_offer_detail_str_shows_title_and_type(self):
        """OfferDetail __str__ is 'offer title (offer_type)'."""
        detail = self.offer.details.get(offer_type="basic")
        self.assertEqual(str(detail), "T (basic)")
