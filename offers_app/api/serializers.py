"""Serializers for the offers_app API."""

from django.db import transaction
from django.urls import reverse
from rest_framework import serializers

from offers_app.models import (
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
    Offer,
    OfferDetail,
    OfferType,
)


def price_field(**kwargs):
    """Return a numeric (non-string) decimal price field."""
    return serializers.DecimalField(
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        coerce_to_string=False,
        **kwargs,
    )


class OfferDetailSerializer(serializers.ModelSerializer):
    """Full offer detail for creation input and detail retrieval."""

    price = price_field()
    features = serializers.JSONField()

    class Meta:
        """Full detail fields in the documented response order."""

        model = OfferDetail
        fields = [
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """A hyperlink stub ``{id, url}`` for an offer's detail."""

    url = serializers.SerializerMethodField()

    class Meta:
        """Only the id and absolute detail url."""

        model = OfferDetail
        fields = ["id", "url"]

    def get_url(self, obj):
        """Return the absolute offerdetails URL including /api/."""
        request = self.context["request"]
        path = reverse("offerdetail-detail", args=[obj.id])
        return request.build_absolute_uri(path)


class OfferCreateSerializer(serializers.ModelSerializer):
    """Validate and atomically create an offer with three details."""

    details = OfferDetailSerializer(many=True)

    class Meta:
        """Create request and response fields in documented order."""

        model = Offer
        fields = ["id", "title", "image", "description", "details"]

    def validate_details(self, value):
        """Require exactly one basic, standard and premium detail."""
        types = sorted(detail["offer_type"] for detail in value)
        if types != sorted(OfferType.values):
            raise serializers.ValidationError(
                "Provide exactly one basic, standard and premium detail."
            )
        return value

    def create(self, validated_data):
        """Create the offer and its details in one transaction."""
        details = validated_data.pop("details")
        user = self.context["request"].user
        with transaction.atomic():
            offer = Offer.objects.create(user=user, **validated_data)
            OfferDetail.objects.bulk_create(
                OfferDetail(offer=offer, **detail) for detail in details
            )
        return offer


class OfferRetrieveSerializer(serializers.ModelSerializer):
    """Full offer representation with detail links and minimums."""

    user = serializers.IntegerField(source="user_id", read_only=True)
    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = price_field(read_only=True)
    min_delivery_time = serializers.IntegerField(read_only=True)

    class Meta:
        """Detail-read fields in the documented response order."""

        model = Offer
        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price",
            "min_delivery_time",
        ]
