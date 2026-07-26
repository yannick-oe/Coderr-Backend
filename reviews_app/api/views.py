"""API views for the reviews_app app."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated

from reviews_app.api.filters import ReviewFilter
from reviews_app.api.permissions import (
    HasNoExistingReview,
    IsReviewAuthor,
    IsReviewCustomer,
)
from reviews_app.api.serializers import (
    ReviewSerializer,
    ReviewUpdateSerializer,
)
from reviews_app.models import Review


class ReviewListCreateView(ListCreateAPIView):
    """List reviews (any authenticated user) or create one (customer)."""

    serializer_class = ReviewSerializer
    pagination_class = None
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ReviewFilter
    ordering_fields = ["updated_at", "rating"]
    ordering = ["-updated_at", "-id"]

    def get_queryset(self):
        """Preload both user rows so the list stays query-constant."""
        return Review.objects.select_related("business_user", "reviewer")

    def get_permissions(self):
        """Any authenticated user lists; only new customers create."""
        if self.request.method == "POST":
            return [
                IsAuthenticated(),
                IsReviewCustomer(),
                HasNoExistingReview(),
            ]
        return [IsAuthenticated()]


class ReviewUpdateDestroyView(
    UpdateModelMixin, DestroyModelMixin, GenericAPIView
):
    """Update or delete a review; only its author may do so."""

    queryset = Review.objects.all()
    serializer_class = ReviewUpdateSerializer
    permission_classes = [IsAuthenticated, IsReviewAuthor]
    http_method_names = ["patch", "delete", "head", "options"]

    def patch(self, request, *args, **kwargs):
        """Partially update the review's rating or description."""
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Delete the review."""
        return self.destroy(request, *args, **kwargs)
