"""Tests for the business and customer list endpoints."""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import ProfileType
from auth_app.tests.utils import authenticate, create_profile

BUSINESS_URL = "/api/profiles/business/"
CUSTOMER_URL = "/api/profiles/customer/"
BUSINESS_KEYS = [
    "user",
    "username",
    "first_name",
    "last_name",
    "file",
    "location",
    "tel",
    "description",
    "working_hours",
    "type",
]
CUSTOMER_KEYS = [
    "user",
    "username",
    "first_name",
    "last_name",
    "file",
    "uploaded_at",
    "type",
]


class ProfileListTests(APITestCase):
    """Business and customer list access, shape and filtering."""

    def setUp(self):
        """Create one business and one customer profile."""
        self.biz = create_profile("biz", ProfileType.BUSINESS)
        self.cust = create_profile("cust", ProfileType.CUSTOMER)
        self.viewer = User.objects.create_user(username="viewer")

    def test_business_list_is_bare_array_with_keys(self):
        """The business list is a bare array with the exact keys."""
        authenticate(self.client, self.viewer)
        response = self.client.get(BUSINESS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(list(response.data[0]), BUSINESS_KEYS)

    def test_business_list_only_contains_business(self):
        """The business list contains only business profiles."""
        authenticate(self.client, self.viewer)
        response = self.client.get(BUSINESS_URL)
        types = {item["type"] for item in response.data}
        self.assertEqual(types, {ProfileType.BUSINESS})

    def test_business_list_requires_auth(self):
        """The business list returns 401 when unauthenticated."""
        response = self.client.get(BUSINESS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_list_is_bare_array_with_keys(self):
        """The customer list is a bare array with the exact keys."""
        authenticate(self.client, self.viewer)
        response = self.client.get(CUSTOMER_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(list(response.data[0]), CUSTOMER_KEYS)

    def test_customer_list_only_contains_customer(self):
        """The customer list contains only customer profiles."""
        authenticate(self.client, self.viewer)
        response = self.client.get(CUSTOMER_URL)
        types = {item["type"] for item in response.data}
        self.assertEqual(types, {ProfileType.CUSTOMER})

    def test_customer_list_requires_auth(self):
        """The customer list returns 401 when unauthenticated."""
        response = self.client.get(CUSTOMER_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
