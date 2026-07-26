"""Tests for the order status-update endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from orders_app.tests.utils import (
    ORDER_KEYS,
    authenticate,
    make_order,
    make_user,
)


class OrderStatusTests(APITestCase):
    """PATCH /api/orders/{id}/ permissions and validation."""

    def setUp(self):
        """Create the order plus customer, owner and other business."""
        self.customer = make_user("cust", ProfileType.CUSTOMER)
        self.business = make_user("biz", ProfileType.BUSINESS)
        self.other_biz = make_user("biz2", ProfileType.BUSINESS)
        self.order = make_order(self.customer, self.business)

    def url(self):
        """Return the order detail path."""
        return f"/api/orders/{self.order.id}/"

    def patch(self, body, user=None):
        """PATCH the order, optionally authenticating first."""
        if user is not None:
            authenticate(self.client, user)
        return self.client.patch(self.url(), body, format="json")

    def test_assigned_business_updates_status_200(self):
        """The assigned business updates status and gets 200."""
        response = self.patch({"status": "completed"}, self.business)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data), ORDER_KEYS)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "completed")

    def test_different_business_403(self):
        """A different business user cannot update the order."""
        response = self.patch({"status": "completed"}, self.other_biz)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_cannot_update_403(self):
        """The customer cannot update the order status."""
        response = self.patch({"status": "completed"}, self.customer)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_401(self):
        """An unauthenticated status update returns 401."""
        response = self.patch({"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_order_404(self):
        """A status update on an unknown order returns 404."""
        authenticate(self.client, self.business)
        response = self.client.patch(
            "/api/orders/99999/", {"status": "completed"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_status_value_400(self):
        """A status outside the allowed set returns 400."""
        response = self.patch({"status": "shipped"}, self.business)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_extra_field_alongside_status_400(self):
        """Any field other than status returns 400."""
        body = {"status": "completed", "price": 5}
        response = self.patch(body, self.business)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
