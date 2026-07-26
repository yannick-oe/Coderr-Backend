"""Serializers for the orders_app API."""

from rest_framework import serializers
from rest_framework.exceptions import NotFound

from offers_app.models import OfferDetail
from orders_app.models import (
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
    Order,
)


def price_field(**kwargs):
    """Return a numeric (non-string) decimal price field."""
    return serializers.DecimalField(
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        coerce_to_string=False,
        **kwargs,
    )


def build_order(detail, customer):
    """Create an order snapshotting the given offer detail."""
    return Order.objects.create(
        customer_user=customer,
        business_user=detail.offer.user,
        title=detail.title,
        revisions=detail.revisions,
        delivery_time_in_days=detail.delivery_time_in_days,
        price=detail.price,
        features=detail.features,
        offer_type=detail.offer_type,
    )


class OrderSerializer(serializers.ModelSerializer):
    """The shared order response shape in documented field order."""

    customer_user = serializers.IntegerField(
        source="customer_user_id", read_only=True
    )
    business_user = serializers.IntegerField(
        source="business_user_id", read_only=True
    )
    price = price_field(read_only=True)

    class Meta:
        """Order response fields in the documented order."""

        model = Order
        fields = [
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


class OrderCreateSerializer(serializers.Serializer):
    """Create an order from an offer detail id."""

    offer_detail_id = serializers.IntegerField(write_only=True)

    def create(self, validated_data):
        """Look up the offer detail and snapshot it into an order."""
        detail = (
            OfferDetail.objects.select_related("offer__user")
            .filter(pk=validated_data["offer_detail_id"])
            .first()
        )
        if detail is None:
            raise NotFound("No offer detail has that id.")
        return build_order(detail, self.context["request"].user)

    def to_representation(self, instance):
        """Render the created order in the shared response shape."""
        return OrderSerializer(instance, context=self.context).data


class OrderStatusSerializer(serializers.ModelSerializer):
    """Update only the status; reject any other field in the body."""

    class Meta:
        """Status is the single writable field."""

        model = Order
        fields = ["status"]

    def validate(self, attrs):
        """Reject any field in the request body other than status."""
        extra = set(self.initial_data) - {"status"}
        if extra:
            raise serializers.ValidationError(
                "Only the status field may be updated."
            )
        return attrs

    def to_representation(self, instance):
        """Render the updated order in the shared response shape."""
        return OrderSerializer(instance, context=self.context).data
