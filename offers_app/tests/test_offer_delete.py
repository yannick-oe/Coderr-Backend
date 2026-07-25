"""Tests for the offer delete endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from offers_app.models import Offer, OfferDetail
from offers_app.tests.utils import authenticate, create_offer, make_user


class OfferDeleteTests(APITestCase):
    """DELETE /api/offers/{id}/ ownership and cascade."""

    def setUp(self):
        """Create an owner, another business user and an offer."""
        self.owner = make_user("owner", ProfileType.BUSINESS)
        self.other = make_user("other", ProfileType.BUSINESS)
        self.offer = create_offer(self.owner)

    def url(self):
        """Return the offer detail path."""
        return f"/api/offers/{self.offer.id}/"

    def test_owner_delete_returns_204_empty_body(self):
        """The owner deletes the offer with 204 and no body."""
        authenticate(self.client, self.owner)
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")

    def test_delete_removes_details(self):
        """Deleting an offer removes its details."""
        authenticate(self.client, self.owner)
        self.client.delete(self.url())
        self.assertEqual(Offer.objects.count(), 0)
        self.assertEqual(OfferDetail.objects.count(), 0)

    def test_other_user_delete_returns_403(self):
        """A non-owner business user cannot delete the offer."""
        authenticate(self.client, self.other)
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_delete_returns_401(self):
        """An unauthenticated delete returns 401."""
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_id_delete_returns_404(self):
        """Deleting an unknown offer id returns 404."""
        authenticate(self.client, self.owner)
        response = self.client.delete("/api/offers/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
