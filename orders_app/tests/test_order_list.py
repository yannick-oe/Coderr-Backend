"""Tests for the order list endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from orders_app.tests.utils import (
    ORDER_KEYS,
    authenticate,
    make_order,
    make_user,
)

ORDERS_URL = "/api/orders/"


class OrderListTests(APITestCase):
    """GET /api/orders/ scoping and shape."""

    def setUp(self):
        """Create a customer, a business and one order between them."""
        self.customer = make_user("cust", ProfileType.CUSTOMER)
        self.business = make_user("biz", ProfileType.BUSINESS)
        self.order = make_order(self.customer, self.business)

    def test_customer_sees_their_order(self):
        """The customer sees the order they placed."""
        authenticate(self.client, self.customer)
        response = self.client.get(ORDERS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([o["id"] for o in response.data], [self.order.id])

    def test_business_sees_their_order(self):
        """The business sees the order assigned to them."""
        authenticate(self.client, self.business)
        response = self.client.get(ORDERS_URL)
        self.assertEqual([o["id"] for o in response.data], [self.order.id])

    def test_uninvolved_user_sees_nothing(self):
        """A third user sees none of the order."""
        authenticate(self.client, make_user("third", ProfileType.CUSTOMER))
        response = self.client.get(ORDERS_URL)
        self.assertEqual(list(response.data), [])

    def test_response_is_bare_list(self):
        """The list response is a bare array."""
        authenticate(self.client, self.customer)
        response = self.client.get(ORDERS_URL)
        self.assertIsInstance(response.data, list)

    def test_item_keys_in_order(self):
        """Each order item has the exact key order."""
        authenticate(self.client, self.customer)
        response = self.client.get(ORDERS_URL)
        self.assertEqual(list(response.data[0]), ORDER_KEYS)

    def test_unauthenticated_returns_401(self):
        """An unauthenticated list returns 401."""
        response = self.client.get(ORDERS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
