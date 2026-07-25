"""Serializers for the auth_app API."""

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer

from auth_app.models import ProfileType, UserProfile

BLANK_FIELDS = (
    "first_name",
    "last_name",
    "location",
    "tel",
    "description",
    "working_hours",
    "file",
)


def blank_none(data, fields):
    """Replace None with an empty string for present fields."""
    for field in fields:
        if field in data and data[field] is None:
            data[field] = ""
    return data


def update_user_fields(user, data):
    """Persist provided User fields (first_name, last_name, email)."""
    if not data:
        return
    for field, value in data.items():
        setattr(user, field, value)
    user.save(update_fields=list(data.keys()))


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


class BaseProfileSerializer(serializers.ModelSerializer):
    """Shared flat profile representation with blank-safe output."""

    user = serializers.IntegerField(source="user_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    def to_representation(self, instance):
        """Serialize the profile, emitting "" instead of null."""
        data = super().to_representation(instance)
        return blank_none(data, BLANK_FIELDS)


class ProfileDetailSerializer(BaseProfileSerializer):
    """Flat profile for retrieve and partial update."""

    first_name = serializers.CharField(
        source="user.first_name", required=False, allow_blank=True
    )
    last_name = serializers.CharField(
        source="user.last_name", required=False, allow_blank=True
    )
    email = serializers.EmailField(source="user.email", required=False)

    class Meta:
        """Flat detail fields in the documented response order."""

        model = UserProfile
        fields = [
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
            "email",
            "created_at",
        ]
        read_only_fields = ["type", "created_at"]

    def update(self, instance, validated_data):
        """Write user fields to User and the rest to the profile."""
        user_data = validated_data.pop("user", {})
        with transaction.atomic():
            update_user_fields(instance.user, user_data)
            instance = super().update(instance, validated_data)
        return instance


class BusinessProfileSerializer(BaseProfileSerializer):
    """Business profile fields for the business list endpoint."""

    first_name = serializers.CharField(
        source="user.first_name", read_only=True
    )
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        """Business list fields in the documented response order."""

        model = UserProfile
        fields = [
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


class CustomerProfileSerializer(BaseProfileSerializer):
    """Customer profile fields for the customer list endpoint."""

    first_name = serializers.CharField(
        source="user.first_name", read_only=True
    )
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    uploaded_at = serializers.DateTimeField(
        source="created_at", read_only=True
    )

    class Meta:
        """Customer list fields in the documented response order."""

        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "uploaded_at",
            "type",
        ]
