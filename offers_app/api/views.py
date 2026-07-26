"""API views for the offers_app app."""

from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    IsAuthenticated,
)

from offers_app.api.filters import OfferFilter
from offers_app.api.pagination import OfferPagination
from offers_app.api.permissions import IsBusinessUser, IsOfferOwnerOrReadOnly
from offers_app.api.serializers import (
    OfferCreateSerializer,
    OfferDetailSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferUpdateSerializer,
)
from offers_app.models import Offer, OfferDetail


def annotated_offers():
    """Return offers with detail minimums, user and details loaded."""
    return (
        Offer.objects.select_related("user")
        .prefetch_related("details")
        .annotate(
            min_price=Min("details__price"),
            min_delivery_time=Min("details__delivery_time_in_days"),
        )
    )


class OfferListCreateView(ListCreateAPIView):
    """List offers publicly or create one as a business user."""

    pagination_class = OfferPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OfferFilter
    search_fields = ["title", "description"]
    ordering_fields = ["updated_at", "min_price"]
    ordering = ["-created_at", "-id"]

    def get_queryset(self):
        """Annotate minimums before filtering and ordering."""
        return annotated_offers()

    def get_serializer_class(self):
        """List with the list serializer, create with the create one."""
        if self.request.method == "POST":
            return OfferCreateSerializer
        return OfferListSerializer

    def get_permissions(self):
        """Public list; business-only create."""
        if self.request.method == "POST":
            return [IsAuthenticated(), IsBusinessUser()]
        return [AllowAny()]


class OfferRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    """Retrieve, partially update, or delete an offer as its owner."""

    permission_classes = [IsAuthenticated, IsOfferOwnerOrReadOnly]
    parser_classes = [MultiPartParser, JSONParser]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        """Annotate and prefetch for reads; stay lean for writes."""
        if self.request.method not in SAFE_METHODS:
            return Offer.objects.select_related("user")
        return annotated_offers()

    def get_serializer_class(self):
        """Read serializer for GET, update serializer for PATCH."""
        if self.request.method == "PATCH":
            return OfferUpdateSerializer
        return OfferRetrieveSerializer


class OfferDetailRetrieveView(RetrieveAPIView):
    """Retrieve a single offer detail in a single query."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]
