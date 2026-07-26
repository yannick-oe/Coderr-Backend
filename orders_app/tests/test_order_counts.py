"""Tests for the order-count endpoints."""

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from orders_app.models import OrderStatus
from orders_app.tests.utils import authenticate, make_order, make_user


class OrderCountTests(APITestCase):
    """GET order-count and completed-order-count endpoints."""

    def setUp(self):
        """Create two in-progress and one completed order."""
        self.customer = make_user("cust", ProfileType.CUSTOMER)
        self.business = make_user("biz", ProfileType.BUSINESS)
        make_order(self.customer, self.business, OrderStatus.IN_PROGRESS)
        make_order(self.customer, self.business, OrderStatus.IN_PROGRESS)
        make_order(self.customer, self.business, OrderStatus.COMPLETED)
        authenticate(self.client, self.customer)

    def count_url(self):
        """Return the in-progress count path for the business user."""
        return f"/api/order-count/{self.business.id}/"

    def completed_url(self):
        """Return the completed count path for the business user."""
        return f"/api/completed-order-count/{self.business.id}/"

    def test_order_count_counts_in_progress(self):
        """order_count returns the number of in-progress orders."""
        response = self.client.get(self.count_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"order_count": 2})

    def test_completed_count_counts_completed(self):
        """completed_order_count returns the completed order count."""
        response = self.client.get(self.completed_url())
        self.assertEqual(response.data, {"completed_order_count": 1})

    def test_unknown_id_returns_404(self):
        """An unknown business_user_id returns 404."""
        response = self.client.get("/api/order-count/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_id_returns_404(self):
        """A customer id (no business profile) returns 404."""
        response = self.client.get(f"/api/order-count/{self.customer.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_count_unauthenticated_401(self):
        """An unauthenticated order-count returns 401."""
        self.client.credentials()
        response = self.client.get(self.count_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_completed_count_unauthenticated_401(self):
        """An unauthenticated completed-order-count returns 401."""
        self.client.credentials()
        response = self.client.get(self.completed_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
