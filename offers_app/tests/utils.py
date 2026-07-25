"""Shared helpers for the offers_app tests."""

from copy import deepcopy

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from auth_app.models import UserProfile
from offers_app.models import Offer, OfferDetail, OfferType

VALID_DETAILS = [
    {
        "title": "Basic",
        "revisions": 2,
        "delivery_time_in_days": 5,
        "price": 100,
        "features": ["Logo"],
        "offer_type": OfferType.BASIC,
    },
    {
        "title": "Standard",
        "revisions": 5,
        "delivery_time_in_days": 7,
        "price": 200,
        "features": ["Logo", "Card"],
        "offer_type": OfferType.STANDARD,
    },
    {
        "title": "Premium",
        "revisions": 10,
        "delivery_time_in_days": 10,
        "price": 500,
        "features": ["Logo", "Card", "Flyer"],
        "offer_type": OfferType.PREMIUM,
    },
]

DETAIL_SPECS = [
    (OfferType.BASIC, 100, 7),
    (OfferType.STANDARD, 200, 5),
    (OfferType.PREMIUM, 500, 10),
]


def make_user(username, profile_type):
    """Create a user with a profile of the given type."""
    user = User.objects.create_user(username=username)
    UserProfile.objects.create(user=user, type=profile_type)
    return user


def authenticate(client, user):
    """Attach the user's token credentials to the API client."""
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")


def offer_payload(**overrides):
    """Return a valid offer creation payload."""
    data = {
        "title": "Design package",
        "image": None,
        "description": "A package.",
        "details": deepcopy(VALID_DETAILS),
    }
    data.update(overrides)
    return data


def create_offer(user):
    """Create an offer with three priced detail tiers."""
    offer = Offer.objects.create(user=user, title="T", description="D")
    for offer_type, price, days in DETAIL_SPECS:
        OfferDetail.objects.create(
            offer=offer,
            title="Tier",
            revisions=1,
            delivery_time_in_days=days,
            price=price,
            features=["f"],
            offer_type=offer_type,
        )
    return offer
