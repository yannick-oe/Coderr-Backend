"""Shared helpers for the auth_app profile tests."""

from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.authtoken.models import Token

from auth_app.models import UserProfile


def create_profile(username, profile_type, *, user_kwargs=None, **fields):
    """Create a user and profile, returning the profile."""
    user = User.objects.create_user(username=username, **(user_kwargs or {}))
    return UserProfile.objects.create(user=user, type=profile_type, **fields)


def authenticate(client, user):
    """Attach the user's token credentials to the API client."""
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")


def make_image(name="avatar.png"):
    """Return a small valid in-memory PNG upload."""
    buffer = BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), "image/png")
