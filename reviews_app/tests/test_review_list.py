"""Tests for the review list endpoint."""

from datetime import timedelta

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from reviews_app.models import Review
from reviews_app.tests.utils import (
    REVIEW_KEYS,
    authenticate,
    make_review,
    make_user,
)

REVIEWS_URL = "/api/reviews/"


class ReviewListTests(APITestCase):
    """GET /api/reviews/ shape, filtering and ordering."""

    def setUp(self):
        """Create three reviews with distinct ratings and times."""
        self.b1 = make_user("b1", ProfileType.BUSINESS)
        self.b2 = make_user("b2", ProfileType.BUSINESS)
        self.c1 = make_user("c1", ProfileType.CUSTOMER)
        self.c2 = make_user("c2", ProfileType.CUSTOMER)
        self.r1 = make_review(self.b1, self.c1, rating=5)
        self.r2 = make_review(self.b2, self.c1, rating=3)
        self.r3 = make_review(self.b1, self.c2, rating=4)
        self.stagger_updated_at()
        authenticate(self.client, self.c1)

    def stagger_updated_at(self):
        """Give r1 < r2 < r3 strictly increasing updated_at values."""
        base = timezone.now()
        for index, review in enumerate([self.r1, self.r2, self.r3]):
            Review.objects.filter(pk=review.pk).update(
                updated_at=base + timedelta(minutes=index)
            )

    def ids(self, query=""):
        """Return the ordered list of result ids for a query."""
        response = self.client.get(f"{REVIEWS_URL}{query}")
        return [item["id"] for item in response.data]

    def test_list_is_bare_list(self):
        """The list response is a bare array."""
        response = self.client.get(REVIEWS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_item_keys_in_order(self):
        """Each review has the exact key order."""
        response = self.client.get(REVIEWS_URL)
        self.assertEqual(list(response.data[0]), REVIEW_KEYS)

    def test_unauthenticated_returns_401(self):
        """An unauthenticated list returns 401."""
        self.client.credentials()
        response = self.client.get(REVIEWS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_filter_business_user_id(self):
        """business_user_id keeps only that business's reviews."""
        got = set(self.ids(f"?business_user_id={self.b1.id}"))
        self.assertEqual(got, {self.r1.id, self.r3.id})

    def test_filter_reviewer_id(self):
        """reviewer_id keeps only that author's reviews."""
        got = set(self.ids(f"?reviewer_id={self.c1.id}"))
        self.assertEqual(got, {self.r1.id, self.r2.id})

    def test_empty_filters_return_all(self):
        """Empty filter values return every review."""
        got = set(self.ids("?business_user_id=&reviewer_id="))
        self.assertEqual(got, {self.r1.id, self.r2.id, self.r3.id})

    def test_order_by_rating_ascending(self):
        """rating sorts lowest first."""
        self.assertEqual(
            self.ids("?ordering=rating"),
            [self.r2.id, self.r3.id, self.r1.id],
        )

    def test_order_by_rating_descending(self):
        """-rating sorts highest first."""
        self.assertEqual(
            self.ids("?ordering=-rating"),
            [self.r1.id, self.r3.id, self.r2.id],
        )

    def test_order_by_updated_at_ascending(self):
        """updated_at sorts oldest first."""
        self.assertEqual(
            self.ids("?ordering=updated_at"),
            [self.r1.id, self.r2.id, self.r3.id],
        )

    def test_order_by_updated_at_descending(self):
        """-updated_at sorts newest first."""
        self.assertEqual(
            self.ids("?ordering=-updated_at"),
            [self.r3.id, self.r2.id, self.r1.id],
        )

    def test_list_query_count_is_constant(self):
        """The list uses the same query count for three and one review."""
        with CaptureQueriesContext(connection) as many:
            self.client.get(REVIEWS_URL)
        Review.objects.exclude(pk=self.r1.pk).delete()
        with CaptureQueriesContext(connection) as few:
            self.client.get(REVIEWS_URL)
        self.assertEqual(len(many.captured_queries), len(few.captured_queries))
