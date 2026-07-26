"""Tests for the order create endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from orders_app.models import Order, OrderStatus
from orders_app.tests.utils import (
    ORDER_KEYS,
    authenticate,
    make_offer_detail,
    make_user,
)

ORDERS_URL = "/api/orders/"


class OrderCreateTests(APITestCase):
    """POST /api/orders/ snapshotting, permissions and status codes."""

    def setUp(self):
        """Create a customer, a business and a source offer detail."""
        self.customer = make_user("cust", ProfileType.CUSTOMER)
        self.business = make_user("biz", ProfileType.BUSINESS)
        self.detail = make_offer_detail(self.business)

    def create(self, body):
        """POST an order body as JSON."""
        return self.client.post(ORDERS_URL, body, format="json")

    def test_customer_creates_order_201(self):
        """A customer creates an order and gets 201 with exact keys."""
        authenticate(self.client, self.customer)
        response = self.create({"offer_detail_id": self.detail.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(list(response.data), ORDER_KEYS)

    def test_snapshot_matches_source_detail(self):
        """Every snapshot field matches the source offer detail."""
        authenticate(self.client, self.customer)
        self.create({"offer_detail_id": self.detail.id})
        order = Order.objects.get()
        self.assertEqual(order.title, self.detail.title)
        self.assertEqual(order.price, self.detail.price)
        self.assertEqual(order.revisions, self.detail.revisions)
        self.assertEqual(order.features, self.detail.features)

    def test_parties_and_initial_status(self):
        """Parties come from auth and offer; status is in_progress."""
        authenticate(self.client, self.customer)
        self.create({"offer_detail_id": self.detail.id})
        order = Order.objects.get()
        self.assertEqual(order.customer_user, self.customer)
        self.assertEqual(order.business_user, self.business)
        self.assertEqual(order.status, OrderStatus.IN_PROGRESS)

    def test_business_cannot_create_403(self):
        """A business user cannot create an order."""
        authenticate(self.client, self.business)
        response = self.create({"offer_detail_id": self.detail.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_create_401(self):
        """An unauthenticated create returns 401."""
        response = self.create({"offer_detail_id": self.detail.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_offer_detail_id_400(self):
        """A missing offer_detail_id returns 400."""
        authenticate(self.client, self.customer)
        self.assertEqual(
            self.create({}).status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_non_integer_offer_detail_id_400(self):
        """A non-integer offer_detail_id returns 400."""
        authenticate(self.client, self.customer)
        response = self.create({"offer_detail_id": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_offer_detail_id_404(self):
        """A well-formed but unknown offer_detail_id returns 404."""
        authenticate(self.client, self.customer)
        response = self.create({"offer_detail_id": 99999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patching_source_detail_leaves_order_unchanged(self):
        """Editing the source detail does not touch the order."""
        authenticate(self.client, self.customer)
        self.create({"offer_detail_id": self.detail.id})
        order = Order.objects.get()
        self.detail.price = 999
        self.detail.save()
        order.refresh_from_db()
        self.assertEqual(order.price, 150)

    def test_deleting_source_offer_leaves_order_intact(self):
        """Deleting the source offer leaves the order in place."""
        authenticate(self.client, self.customer)
        self.create({"offer_detail_id": self.detail.id})
        self.detail.offer.delete()
        self.assertEqual(Order.objects.count(), 1)
