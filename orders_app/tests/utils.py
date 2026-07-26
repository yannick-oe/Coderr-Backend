"""Shared helpers for the orders_app tests."""

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from auth_app.models import UserProfile
from offers_app.models import Offer, OfferDetail, OfferType
from orders_app.models import Order, OrderStatus

ORDER_KEYS = [
    "id",
    "customer_user",
    "business_user",
    "title",
    "revisions",
    "delivery_time_in_days",
    "price",
    "features",
    "offer_type",
    "status",
    "created_at",
    "updated_at",
]


def make_user(username, profile_type):
    """Create a user with a profile of the given type."""
    user = User.objects.create_user(username=username)
    UserProfile.objects.create(user=user, type=profile_type)
    return user


def make_staff(username):
    """Create a staff user without a profile."""
    return User.objects.create_user(username=username, is_staff=True)


def authenticate(client, user):
    """Attach the user's token credentials to the API client."""
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")


def make_offer_detail(business):
    """Create an offer owned by business with one basic detail."""
    offer = Offer.objects.create(user=business, title="Logo", description="D")
    return OfferDetail.objects.create(
        offer=offer,
        title="Basic",
        revisions=3,
        delivery_time_in_days=5,
        price=150,
        features=["Logo", "Card"],
        offer_type=OfferType.BASIC,
    )


def make_order(customer, business, status=OrderStatus.IN_PROGRESS):
    """Create an order between a customer and a business user."""
    return Order.objects.create(
        customer_user=customer,
        business_user=business,
        status=status,
        title="Logo",
        revisions=3,
        delivery_time_in_days=5,
        price=150,
        features=["Logo"],
        offer_type=OfferType.BASIC,
    )
