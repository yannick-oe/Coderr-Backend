"""Tests for the review create endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from reviews_app.tests.utils import REVIEW_KEYS, authenticate, make_user

REVIEWS_URL = "/api/reviews/"


class ReviewCreateTests(APITestCase):
    """POST /api/reviews/ permissions, validation and uniqueness."""

    def setUp(self):
        """Create two business and two customer users."""
        self.business = make_user("biz", ProfileType.BUSINESS)
        self.business2 = make_user("biz2", ProfileType.BUSINESS)
        self.customer = make_user("cust", ProfileType.CUSTOMER)
        self.customer2 = make_user("cust2", ProfileType.CUSTOMER)

    def create(self, body, user=None):
        """POST a review body, optionally authenticating first."""
        if user is not None:
            authenticate(self.client, user)
        return self.client.post(REVIEWS_URL, body, format="json")

    def body(self, **overrides):
        """Return a valid review payload with optional overrides."""
        data = {
            "business_user": self.business.id,
            "rating": 4,
            "description": "Great",
        }
        data.update(overrides)
        return data

    def test_customer_creates_201_and_keys(self):
        """A customer creates a review and gets 201 with exact keys."""
        response = self.create(self.body(), self.customer)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list(response.data), REVIEW_KEYS)

    def test_reviewer_taken_from_request(self):
        """The reviewer is the authenticated user."""
        response = self.create(self.body(), self.customer)
        self.assertEqual(response.data["reviewer"], self.customer.id)

    def test_reviewer_in_body_is_ignored(self):
        """A reviewer field in the body is ignored."""
        body = self.body(reviewer=self.customer2.id)
        response = self.create(body, self.customer)
        self.assertEqual(response.data["reviewer"], self.customer.id)

    def test_business_user_cannot_create_403(self):
        """A business user cannot create a review."""
        response = self.create(self.body(), self.business)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_create_401(self):
        """An unauthenticated create returns 401."""
        response = self.create(self.body())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_returns_403(self):
        """A second review of the same business returns 403."""
        self.create(self.body(), self.customer)
        response = self.create(self.body(), self.customer)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_different_business_same_reviewer_201(self):
        """The same reviewer may review a different business."""
        self.create(self.body(), self.customer)
        body = self.body(business_user=self.business2.id)
        response = self.create(body, self.customer)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_same_business_different_reviewer_201(self):
        """A different reviewer may review the same business."""
        self.create(self.body(), self.customer)
        response = self.create(self.body(), self.customer2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_rating_zero_returns_400(self):
        """A rating of 0 is rejected with 400."""
        response = self.create(self.body(rating=0), self.customer)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_six_returns_400(self):
        """A rating of 6 is rejected with 400."""
        response = self.create(self.body(rating=6), self.customer)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_rating_returns_400(self):
        """A missing rating is rejected with 400."""
        body = self.body()
        del body["rating"]
        response = self.create(body, self.customer)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_description_returns_400(self):
        """A missing description is rejected with 400."""
        body = self.body()
        del body["description"]
        response = self.create(body, self.customer)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_business_user_returns_400(self):
        """An unknown business_user is rejected with 400."""
        response = self.create(self.body(business_user=99999), self.customer)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_business_user_returns_400(self):
        """A business_user id belonging to a customer returns 400."""
        body = self.body(business_user=self.customer2.id)
        response = self.create(body, self.customer)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_business_user_returns_400(self):
        """A missing business_user is a serializer 400, not a 500."""
        body = self.body()
        del body["business_user"]
        response = self.create(body, self.customer)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_numeric_business_user_returns_400(self):
        """A non-numeric business_user is a serializer 400, not a 500."""
        body = self.body(business_user="abc")
        response = self.create(body, self.customer)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
