"""Tests for orders_app model string representations."""

from django.test import TestCase

from auth_app.models import ProfileType
from orders_app.tests.utils import make_order, make_user


class OrderStrTests(TestCase):
    """The Order __str__ shown in the admin changelist."""

    def test_str_shows_id_and_status(self):
        """Order __str__ is 'Order #<pk> (<status>)'."""
        customer = make_user("cust", ProfileType.CUSTOMER)
        business = make_user("biz", ProfileType.BUSINESS)
        order = make_order(customer, business)
        self.assertEqual(str(order), f"Order #{order.pk} (in_progress)")
