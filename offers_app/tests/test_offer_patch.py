"""Tests for the offer partial-update (PATCH) endpoint."""

import shutil
import tempfile
from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from offers_app.models import Offer
from offers_app.tests.utils import (
    authenticate,
    create_offer,
    make_image,
    make_user,
)

RESPONSE_KEYS = ["id", "title", "image", "description", "details"]
DETAIL_KEYS = [
    "id",
    "title",
    "revisions",
    "delivery_time_in_days",
    "price",
    "features",
    "offer_type",
]
TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class OfferPatchTests(APITestCase):
    """PATCH /api/offers/{id}/ semantics, permissions and shape."""

    def setUp(self):
        """Create an owner offer and authenticate as the owner."""
        self.owner = make_user("owner", ProfileType.BUSINESS)
        self.other = make_user("other", ProfileType.BUSINESS)
        self.offer = create_offer(self.owner)
        authenticate(self.client, self.owner)

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary media directory."""
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def url(self):
        """Return the offer detail path."""
        return f"/api/offers/{self.offer.id}/"

    def patch(self, payload, fmt="json"):
        """PATCH the owner's offer with a payload."""
        return self.client.patch(self.url(), payload, format=fmt)

    def detail(self, offer_type):
        """Return a fresh detail of the offer by offer_type."""
        return self.offer.details.get(offer_type=offer_type)

    def ignored_payload(self):
        """Return a payload full of read-only and unknown fields."""
        return {
            "title": "Renamed",
            "user": self.other.id,
            "created_at": "2000-01-01T00:00:00Z",
            "min_price": 1,
            "user_details": {"username": "x"},
        }

    def test_update_title_only(self):
        """Updating only the title leaves the description unchanged."""
        original = self.offer.description
        response = self.patch({"title": "New Title"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), RESPONSE_KEYS)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, "New Title")
        self.assertEqual(self.offer.description, original)

    def test_update_description_only(self):
        """Updating only the description leaves the title unchanged."""
        original = self.offer.title
        response = self.patch({"description": "New desc"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.description, "New desc")
        self.assertEqual(self.offer.title, original)

    def test_response_detail_key_order(self):
        """Each response detail carries the exact key order."""
        response = self.patch({"title": "x"})
        self.assertEqual(list(response.data["details"][0]), DETAIL_KEYS)

    def test_update_single_detail_by_offer_type(self):
        """One detail is updated, matched by its offer_type."""
        payload = {"details": [{"offer_type": "basic", "price": 111}]}
        response = self.patch(payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), RESPONSE_KEYS)
        self.assertEqual(self.detail("basic").price, 111)

    def test_update_two_details(self):
        """Two details update in one request."""
        payload = {
            "details": [
                {"offer_type": "basic", "price": 111},
                {"offer_type": "standard", "price": 222},
            ]
        }
        self.assertEqual(self.patch(payload).status_code, status.HTTP_200_OK)
        self.assertEqual(self.detail("basic").price, 111)
        self.assertEqual(self.detail("standard").price, 222)

    def test_update_all_three_details(self):
        """All three details update in one request."""
        payload = {
            "details": [
                {"offer_type": "basic", "price": 1},
                {"offer_type": "standard", "price": 2},
                {"offer_type": "premium", "price": 3},
            ]
        }
        self.assertEqual(self.patch(payload).status_code, status.HTTP_200_OK)
        prices = {d.offer_type: d.price for d in self.offer.details.all()}
        self.assertEqual(prices, {"basic": 1, "standard": 2, "premium": 3})

    def test_detail_ids_unchanged_after_update(self):
        """Detail ids are stable across an update of all three."""
        before = sorted(self.offer.details.values_list("id", flat=True))
        payload = {
            "details": [
                {"offer_type": "basic", "price": 1},
                {"offer_type": "standard", "price": 2},
                {"offer_type": "premium", "price": 3},
            ]
        }
        self.patch(payload)
        after = sorted(self.offer.details.values_list("id", flat=True))
        self.assertEqual(before, after)

    def test_partial_detail_leaves_other_fields(self):
        """A detail entry with only price changes only the price."""
        basic = self.detail("basic")
        self.patch({"details": [{"offer_type": "basic", "price": 999}]})
        updated = self.detail("basic")
        self.assertEqual(updated.price, 999)
        self.assertEqual(updated.title, basic.title)
        self.assertEqual(updated.revisions, basic.revisions)

    def test_revisions_minus_one_accepted(self):
        """revisions = -1 (unlimited) is accepted on update."""
        payload = {"details": [{"offer_type": "basic", "revisions": -1}]}
        response = self.patch(payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.detail("basic").revisions, -1)

    def test_read_only_and_unknown_fields_ignored(self):
        """Read-only and unknown fields are ignored, not applied."""
        created = self.offer.created_at
        response = self.patch(self.ignored_payload())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.user, self.owner)
        self.assertEqual(self.offer.created_at, created)
        self.assertEqual(self.offer.title, "Renamed")

    def test_detail_without_offer_type_returns_400(self):
        """A detail entry without offer_type is a 400."""
        response = self.patch({"details": [{"price": 5}]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_offer_type_returns_400(self):
        """A detail entry with an unknown offer_type is a 400."""
        payload = {"details": [{"offer_type": "gold", "price": 5}]}
        response = self.patch(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_offer_type_returns_400(self):
        """Two entries with the same offer_type is a 400."""
        payload = {
            "details": [
                {"offer_type": "basic", "price": 1},
                {"offer_type": "basic", "price": 2},
            ]
        }
        response = self.patch(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detail_type_absent_on_offer_returns_400(self):
        """Updating a detail type the offer lacks returns 400."""
        self.offer.details.filter(offer_type="premium").delete()
        payload = {"details": [{"offer_type": "premium", "price": 5}]}
        response = self.patch(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_multipart_image_only_succeeds(self):
        """A multipart PATCH carrying only image returns 200."""
        response = self.patch({"image": make_image()}, fmt="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.image)

    def test_patch_by_other_user_returns_403(self):
        """A non-owner business user gets 403."""
        authenticate(self.client, self.other)
        response = self.patch({"title": "x"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_unauthenticated_returns_401(self):
        """An unauthenticated PATCH gets 401."""
        self.client.credentials()
        response = self.patch({"title": "x"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_unknown_id_returns_404(self):
        """A PATCH on an unknown offer id gets 404."""
        response = self.client.patch(
            "/api/offers/99999/", {"title": "x"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_updated_at_advances(self):
        """updated_at moves forward even for a details-only update."""
        old = timezone.now() - timedelta(hours=1)
        Offer.objects.filter(pk=self.offer.pk).update(updated_at=old)
        self.patch({"details": [{"offer_type": "basic", "price": 7}]})
        self.offer.refresh_from_db()
        self.assertGreater(self.offer.updated_at, old)
