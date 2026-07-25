"""Tests for the offer detail read endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from offers_app.tests.utils import authenticate, create_offer, make_user

DETAIL_READ_KEYS = [
    "id",
    "user",
    "title",
    "image",
    "description",
    "created_at",
    "updated_at",
    "details",
    "min_price",
    "min_delivery_time",
]
LINK_KEYS = ["id", "url"]


class OfferDetailReadTests(APITestCase):
    """GET /api/offers/{id}/ access, shape and minimums."""

    def setUp(self):
        """Create a business user and an offer with details."""
        self.business = make_user("biz", ProfileType.BUSINESS)
        self.offer = create_offer(self.business)

    def url(self):
        """Return the offer detail path."""
        return f"/api/offers/{self.offer.id}/"

    def test_read_returns_exact_keys_in_order(self):
        """The read returns 200 with the exact key order."""
        authenticate(self.client, self.business)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), DETAIL_READ_KEYS)

    def test_user_is_integer_id(self):
        """The user field is the creating user's integer id."""
        authenticate(self.client, self.business)
        response = self.client.get(self.url())
        self.assertEqual(response.data["user"], self.business.id)

    def test_details_are_absolute_id_url_links(self):
        """Each detail is an {id, url} link with an absolute /api URL."""
        authenticate(self.client, self.business)
        link = self.client.get(self.url()).data["details"][0]
        self.assertEqual(list(link), LINK_KEYS)
        self.assertTrue(link["url"].startswith("http"))
        self.assertIn("/api/offerdetails/", link["url"])

    def test_min_price_and_delivery_are_minimums(self):
        """min_price and min_delivery_time are the detail minimums."""
        authenticate(self.client, self.business)
        response = self.client.get(self.url())
        self.assertEqual(response.data["min_price"], 100)
        self.assertEqual(response.data["min_delivery_time"], 5)

    def test_min_price_is_number_not_string(self):
        """min_price renders as a JSON number, not a string."""
        authenticate(self.client, self.business)
        value = self.client.get(self.url()).json()["min_price"]
        self.assertIsInstance(value, (int, float))

    def test_unauthenticated_read_returns_401(self):
        """An unauthenticated read returns 401."""
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_id_returns_404(self):
        """A read of an unknown offer id returns 404."""
        authenticate(self.client, self.business)
        response = self.client.get("/api/offers/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
