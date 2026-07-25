"""API views for the offers_app app."""

from django.db.models import Min
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
    RetrieveDestroyAPIView,
)
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated

from offers_app.api.permissions import IsBusinessUser, IsOfferOwnerOrReadOnly
from offers_app.api.serializers import (
    OfferCreateSerializer,
    OfferDetailSerializer,
    OfferRetrieveSerializer,
)
from offers_app.models import Offer, OfferDetail


class OfferCreateView(CreateAPIView):
    """Create a new offer with its three pricing tiers."""

    queryset = Offer.objects.all()
    serializer_class = OfferCreateSerializer
    permission_classes = [IsAuthenticated, IsBusinessUser]


class OfferRetrieveDestroyView(RetrieveDestroyAPIView):
    """Retrieve an offer with minimums or delete it as its owner."""

    serializer_class = OfferRetrieveSerializer
    permission_classes = [IsAuthenticated, IsOfferOwnerOrReadOnly]

    def get_queryset(self):
        """Annotate and prefetch for reads; stay lean for deletes."""
        offers = Offer.objects.select_related("user")
        if self.request.method not in SAFE_METHODS:
            return offers
        return offers.prefetch_related("details").annotate(
            min_price=Min("details__price"),
            min_delivery_time=Min("details__delivery_time_in_days"),
        )


class OfferDetailRetrieveView(RetrieveAPIView):
    """Retrieve a single offer detail in a single query."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
