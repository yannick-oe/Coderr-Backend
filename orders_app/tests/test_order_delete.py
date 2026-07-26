"""Tests for the order delete endpoint."""

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from orders_app.tests.utils import (
    authenticate,
    make_order,
    make_staff,
    make_user,
)


class OrderDeleteTests(APITestCase):
    """DELETE /api/orders/{id}/ is restricted to staff users."""

    def setUp(self):
        """Create the order plus customer, business and staff users."""
        self.customer = make_user("cust", ProfileType.CUSTOMER)
        self.business = make_user("biz", ProfileType.BUSINESS)
        self.staff = make_staff("admin")
        self.order = make_order(self.customer, self.business)

    def url(self):
        """Return the order detail path."""
        return f"/api/orders/{self.order.id}/"

    def test_staff_deletes_204_empty_body(self):
        """A staff user deletes the order with 204 and no body."""
        authenticate(self.client, self.staff)
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")

    def test_assigned_business_cannot_delete_403(self):
        """The assigned business user cannot delete the order."""
        authenticate(self.client, self.business)
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_delete_401(self):
        """An unauthenticated delete returns 401."""
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_order_delete_404(self):
        """Deleting an unknown order id returns 404."""
        authenticate(self.client, self.staff)
        response = self.client.delete("/api/orders/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
