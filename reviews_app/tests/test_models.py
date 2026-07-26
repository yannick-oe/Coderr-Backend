"""Tests for reviews_app model string representations."""

from django.test import TestCase

from auth_app.models import ProfileType
from reviews_app.tests.utils import make_review, make_user


class ReviewStrTests(TestCase):
    """The Review __str__ shown in the admin changelist."""

    def test_str_shows_id_and_rating(self):
        """Review __str__ is 'Review #<pk> (<rating>)'."""
        business = make_user("biz", ProfileType.BUSINESS)
        reviewer = make_user("rev", ProfileType.CUSTOMER)
        review = make_review(business, reviewer, rating=4)
        self.assertEqual(str(review), f"Review #{review.pk} (4)")
