"""Shared helpers for the reviews_app tests."""

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from auth_app.models import UserProfile
from reviews_app.models import Review

REVIEW_KEYS = [
    "id",
    "business_user",
    "reviewer",
    "rating",
    "description",
    "created_at",
    "updated_at",
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


def make_review(business_user, reviewer, rating=4, description="Good"):
    """Create a review between a reviewer and a business user."""
    return Review.objects.create(
        business_user=business_user,
        reviewer=reviewer,
        rating=rating,
        description=description,
    )
