"""Serializers for the auth_app API."""

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer

from auth_app.models import ProfileType, UserProfile


class RegistrationSerializer(serializers.Serializer):
    """Validate and atomically create a user, profile and token."""

    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=ProfileType.choices)

    def validate_username(self, value):
        """Reject a username that is already taken."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "This username is already taken."
            )
        return value

    def validate_email(self, value):
        """Reject an email that is already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "This email is already registered."
            )
        return value

    def validate(self, attrs):
        """Ensure the two password entries match."""
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "The passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        """Create the user, profile and token in one transaction."""
        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data["username"],
                email=validated_data["email"],
                password=validated_data["password"],
            )
            UserProfile.objects.create(user=user, type=validated_data["type"])
            token = Token.objects.create(user=user)
        return {"user": user, "token": token}


class LoginSerializer(AuthTokenSerializer):
    """Validate username and password via the DRF token flow.

    Invalid credentials raise a validation error (HTTP 400), which is
    the status the endpoint documentation prescribes for this endpoint.
    """
