"""Tests for the review delete endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from reviews_app.tests.utils import authenticate, make_review, make_user


class ReviewDeleteTests(APITestCase):
    """DELETE /api/reviews/{id}/ is restricted to the author."""

    def setUp(self):
        """Create a review by the author plus another user."""
        self.business = make_user("biz", ProfileType.BUSINESS)
        self.author = make_user("author", ProfileType.CUSTOMER)
        self.other = make_user("other", ProfileType.CUSTOMER)
        self.review = make_review(self.business, self.author)

    def url(self):
        """Return the review detail path."""
        return f"/api/reviews/{self.review.id}/"

    def test_author_deletes_204_empty_body(self):
        """The author deletes the review with 204 and no body."""
        authenticate(self.client, self.author)
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")

    def test_other_user_403(self):
        """A non-author cannot delete the review."""
        authenticate(self.client, self.other)
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_401(self):
        """An unauthenticated delete returns 401."""
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_id_404(self):
        """Deleting an unknown review id returns 404."""
        authenticate(self.client, self.author)
        response = self.client.delete("/api/reviews/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
