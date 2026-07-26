"""Tests for the offer creation endpoint."""

from unittest import mock

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from offers_app.models import Offer
from offers_app.tests.utils import authenticate, make_user, offer_payload

OFFERS_URL = "/api/offers/"
CREATE_KEYS = ["id", "title", "image", "description", "details"]
DETAIL_KEYS = [
    "id",
    "title",
    "revisions",
    "delivery_time_in_days",
    "price",
    "features",
    "offer_type",
]


class OfferCreateTests(APITestCase):
    """POST /api/offers/ permissions, validation and shape."""

    def setUp(self):
        """Create a business and a customer user."""
        self.business = make_user("biz", ProfileType.BUSINESS)
        self.customer = make_user("cust", ProfileType.CUSTOMER)

    def post(self, payload):
        """Post a payload to the offers endpoint as JSON."""
        return self.client.post(OFFERS_URL, payload, format="json")

    def test_business_create_returns_201_and_keys(self):
        """A business user creates an offer with the exact keys."""
        authenticate(self.client, self.business)
        response = self.post(offer_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list(response.data), CREATE_KEYS)

    def test_created_details_are_full_objects_in_order(self):
        """The response details are full objects, cheapest first."""
        authenticate(self.client, self.business)
        response = self.post(offer_payload())
        self.assertEqual(list(response.data["details"][0]), DETAIL_KEYS)
        types = [d["offer_type"] for d in response.data["details"]]
        self.assertEqual(types, ["basic", "standard", "premium"])

    def test_image_serializes_as_null_when_empty(self):
        """An offer without an image renders image as null."""
        authenticate(self.client, self.business)
        response = self.post(offer_payload())
        self.assertIsNone(response.data["image"])

    def test_owner_taken_from_request_not_body(self):
        """A user field in the body is ignored; owner is the requester."""
        authenticate(self.client, self.business)
        response = self.post(offer_payload(user=self.customer.id))
        offer = Offer.objects.get(id=response.data["id"])
        self.assertEqual(offer.user, self.business)

    def test_customer_cannot_create_offer(self):
        """A customer user is forbidden from creating offers."""
        authenticate(self.client, self.customer)
        response = self.post(offer_payload())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_create_returns_401(self):
        """An unauthenticated create returns 401."""
        response = self.post(offer_payload())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_token_create_returns_401(self):
        """An unknown token still returns 401; the view is not weakened."""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + "a" * 40)
        response = self.post(offer_payload())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_two_details_rejected(self):
        """An offer with only two details is rejected."""
        authenticate(self.client, self.business)
        payload = offer_payload()
        payload["details"] = payload["details"][:2]
        self.assertEqual(
            self.post(payload).status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_duplicate_offer_type_rejected(self):
        """A duplicated offer_type is rejected."""
        authenticate(self.client, self.business)
        payload = offer_payload()
        payload["details"][1]["offer_type"] = "basic"
        self.assertEqual(
            self.post(payload).status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_missing_offer_type_rejected(self):
        """A missing offer_type is rejected."""
        authenticate(self.client, self.business)
        payload = offer_payload()
        del payload["details"][2]["offer_type"]
        self.assertEqual(
            self.post(payload).status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_no_offer_created_on_invalid_details(self):
        """A rejected create leaves no offer behind."""
        authenticate(self.client, self.business)
        payload = offer_payload()
        payload["details"] = payload["details"][:2]
        self.post(payload)
        self.assertEqual(Offer.objects.count(), 0)

    def test_atomic_rollback_on_detail_failure(self):
        """A failure creating details rolls back the offer."""
        authenticate(self.client, self.business)
        target = "offers_app.api.serializers.OfferDetail.objects.bulk_create"
        with mock.patch(target, side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                self.post(offer_payload())
        self.assertEqual(Offer.objects.count(), 0)
