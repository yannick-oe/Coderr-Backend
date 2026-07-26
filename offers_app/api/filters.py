"""Filter definitions for the offers_app API."""

from django_filters import rest_framework as filters

from offers_app.models import Offer


class OfferFilter(filters.FilterSet):
    """Filter offers by creator, minimum price and delivery time.

    ``min_price`` and ``max_delivery_time`` filter the ``min_price`` and
    ``min_delivery_time`` queryset annotations, so the view must annotate
    them before this filter runs. Empty values are treated as no filter.
    """

    creator_id = filters.NumberFilter(field_name="user_id")
    min_price = filters.NumberFilter(field_name="min_price", lookup_expr="gte")
    max_delivery_time = filters.NumberFilter(
        field_name="min_delivery_time", lookup_expr="lte"
    )

    class Meta:
        """Bind the offer filters to their query parameters."""

        model = Offer
        fields = ["creator_id", "min_price", "max_delivery_time"]
