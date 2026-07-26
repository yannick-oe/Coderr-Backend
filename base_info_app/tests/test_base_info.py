"""Tests for the base-info endpoint."""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from auth_app.models import ProfileType, UserProfile
from offers_app.models import Offer
from reviews_app.models import Review

BASE_INFO_URL = "/api/base-info/"
BASE_INFO_KEYS = [
    "review_count",
    "average_rating",
    "business_profile_count",
    "offer_count",
]
UNKNOWN_TOKEN = "Token " + "a" * 40
MALFORMED_HEADER = "Token malformed value"
AUTH_HEADER_CASES = [
    ("none", None),
    ("unknown_token", UNKNOWN_TOKEN),
    ("malformed", MALFORMED_HEADER),
]


def make_profile(username, profile_type):
    """Create a user with a profile of the given type."""
    user = User.objects.create_user(username=username)
    UserProfile.objects.create(user=user, type=profile_type)
    return user


def make_offer(business):
    """Create a minimal offer for a business user."""
    Offer.objects.create(user=business, title="O", description="D")


def make_review(business, reviewer, rating):
    """Create a review with the given rating."""
    Review.objects.create(
        business_user=business,
        reviewer=reviewer,
        rating=rating,
        description="x",
    )


def authenticate(client, user):
    """Attach the user's token credentials to the API client."""
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")


class BaseInfoTests(APITestCase):
    """GET /api/base-info/ shape, values and access."""

    def setUp(self):
        """Create businesses, offers and reviews averaging 4.333."""
        self.b1 = make_profile("b1", ProfileType.BUSINESS)
        self.b2 = make_profile("b2", ProfileType.BUSINESS)
        self.c1 = make_profile("c1", ProfileType.CUSTOMER)
        self.c2 = make_profile("c2", ProfileType.CUSTOMER)
        make_offer(self.b1)
        make_offer(self.b1)
        make_review(self.b1, self.c1, 5)
        make_review(self.b2, self.c1, 4)
        make_review(self.b1, self.c2, 4)

    def test_keys_in_order(self):
        """The response has the exact key set and order."""
        response = self.client.get(BASE_INFO_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), BASE_INFO_KEYS)

    def test_counts_against_fixtures(self):
        """The three counts match the created fixtures."""
        data = self.client.get(BASE_INFO_URL).data
        self.assertEqual(data["review_count"], 3)
        self.assertEqual(data["business_profile_count"], 2)
        self.assertEqual(data["offer_count"], 2)

    def test_average_rating_rounds_to_one_decimal(self):
        """The average of 5, 4, 4 rounds to 4.3."""
        data = self.client.get(BASE_INFO_URL).data
        self.assertEqual(data["average_rating"], 4.3)

    def test_unauthenticated_access_succeeds(self):
        """The endpoint is readable without authentication."""
        response = self.client.get(BASE_INFO_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_access_succeeds(self):
        """The endpoint is also readable when authenticated."""
        authenticate(self.client, self.c1)
        response = self.client.get(BASE_INFO_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BaseInfoEmptyTests(APITestCase):
    """base-info with no reviews yields a zero average, not null."""

    def test_average_rating_is_zero_without_reviews(self):
        """Without reviews, average_rating is 0 and not null."""
        make_profile("b1", ProfileType.BUSINESS)
        data = self.client.get(BASE_INFO_URL).data
        self.assertEqual(data["review_count"], 0)
        self.assertEqual(data["average_rating"], 0)
        self.assertIsNotNone(data["average_rating"])


class BaseInfoIgnoresAuthHeaderTests(APITestCase):
    """base-info returns 200 regardless of any Authorization header."""

    def fetch(self, header):
        """GET base-info under the given auth header."""
        if header is None:
            self.client.credentials()
        else:
            self.client.credentials(HTTP_AUTHORIZATION=header)
        return self.client.get(BASE_INFO_URL)

    def test_returns_200_for_every_header_variant(self):
        """base-info returns 200 with no, unknown, or bad header."""
        for label, header in AUTH_HEADER_CASES:
            with self.subTest(header=label):
                response = self.fetch(header)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
