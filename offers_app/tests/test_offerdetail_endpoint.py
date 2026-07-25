"""Tests for the single offer-detail endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from offers_app.tests.utils import authenticate, create_offer, make_user

OFFERDETAIL_KEYS = [
    "id",
    "title",
    "revisions",
    "delivery_time_in_days",
    "price",
    "features",
    "offer_type",
]


class OfferDetailEndpointTests(APITestCase):
    """GET /api/offerdetails/{id}/ access and shape."""

    def setUp(self):
        """Create a business user, an offer and grab a detail."""
        self.business = make_user("biz", ProfileType.BUSINESS)
        self.offer = create_offer(self.business)
        self.detail = self.offer.details.first()

    def url(self, pk):
        """Return the offer-detail path for a detail id."""
        return f"/api/offerdetails/{pk}/"

    def test_read_returns_exact_keys_in_order(self):
        """The read returns 200 with the exact key order."""
        authenticate(self.client, self.business)
        response = self.client.get(self.url(self.detail.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), OFFERDETAIL_KEYS)

    def test_price_is_number_not_string(self):
        """The price renders as a JSON number, not a string."""
        authenticate(self.client, self.business)
        value = self.client.get(self.url(self.detail.id)).json()["price"]
        self.assertIsInstance(value, (int, float))

    def test_unauthenticated_read_returns_401(self):
        """An unauthenticated read returns 401."""
        response = self.client.get(self.url(self.detail.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_id_returns_404(self):
        """A read of an unknown detail id returns 404."""
        authenticate(self.client, self.business)
        response = self.client.get(self.url(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
