"""Serializers for the reviews_app API."""

from django.contrib.auth.models import User
from rest_framework import serializers

from auth_app.models import ProfileType, UserProfile
from reviews_app.models import Review

RATING_MIN = 1
RATING_MAX = 5


class ReviewSerializer(serializers.ModelSerializer):
    """The shared review shape; used for listing and creation."""

    business_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    reviewer = serializers.IntegerField(source="reviewer_id", read_only=True)
    rating = serializers.IntegerField(
        min_value=RATING_MIN, max_value=RATING_MAX
    )

    class Meta:
        """Review fields in the documented response order."""

        model = Review
        fields = [
            "id",
            "business_user",
            "reviewer",
            "rating",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_business_user(self, value):
        """Require the target to be an existing business account."""
        if not UserProfile.objects.filter(
            user=value, type=ProfileType.BUSINESS
        ).exists():
            raise serializers.ValidationError(
                "business_user must be a business account."
            )
        return value

    def create(self, validated_data):
        """Attach the authenticated user as the reviewer."""
        validated_data["reviewer"] = self.context["request"].user
        return super().create(validated_data)


class ReviewUpdateSerializer(ReviewSerializer):
    """Review update: only rating and description are editable."""

    business_user = serializers.IntegerField(
        source="business_user_id", read_only=True
    )
