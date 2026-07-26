"""Tests for the review update endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from reviews_app.tests.utils import (
    REVIEW_KEYS,
    authenticate,
    make_review,
    make_user,
)


class ReviewUpdateTests(APITestCase):
    """PATCH /api/reviews/{id}/ author-only editing of rating/description."""

    def setUp(self):
        """Create a review by the author plus other users."""
        self.business = make_user("biz", ProfileType.BUSINESS)
        self.business2 = make_user("biz2", ProfileType.BUSINESS)
        self.author = make_user("author", ProfileType.CUSTOMER)
        self.other = make_user("other", ProfileType.CUSTOMER)
        self.review = make_review(self.business, self.author, rating=4)

    def url(self):
        """Return the review detail path."""
        return f"/api/reviews/{self.review.id}/"

    def patch(self, body, user=None):
        """PATCH the review, optionally authenticating first."""
        if user is not None:
            authenticate(self.client, user)
        return self.client.patch(self.url(), body, format="json")

    def test_author_updates_200_and_keys(self):
        """The author updates rating and description with 200."""
        body = {"rating": 5, "description": "Better"}
        response = self.patch(body, self.author)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), REVIEW_KEYS)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 5)

    def test_other_user_403(self):
        """A non-author cannot update the review."""
        response = self.patch({"rating": 5}, self.other)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_401(self):
        """An unauthenticated update returns 401."""
        response = self.patch({"rating": 5})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_id_404(self):
        """An update of an unknown review id returns 404."""
        authenticate(self.client, self.author)
        response = self.client.patch(
            "/api/reviews/99999/", {"rating": 5}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_business_user_change_is_ignored(self):
        """A business_user in the body is ignored, staying unchanged."""
        body = {"rating": 5, "business_user": self.business2.id}
        self.patch(body, self.author)
        self.review.refresh_from_db()
        self.assertEqual(self.review.business_user, self.business)

    def test_invalid_rating_400(self):
        """A rating outside 1-5 returns 400."""
        response = self.patch({"rating": 6}, self.author)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
