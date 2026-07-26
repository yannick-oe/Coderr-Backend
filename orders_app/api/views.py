"""API views for the orders_app app."""

from django.db.models import Q
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import ProfileType, UserProfile
from orders_app.api.permissions import (
    IsAssignedBusinessUser,
    IsCustomerUser,
)
from orders_app.api.serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusSerializer,
)
from orders_app.models import Order, OrderStatus


def get_business_user_or_404(user_id):
    """Ensure a business-profile user exists for the id, else 404."""
    if not UserProfile.objects.filter(
        user_id=user_id, type=ProfileType.BUSINESS
    ).exists():
        raise NotFound("No business user has that id.")


class OrderListCreateView(ListCreateAPIView):
    """List the caller's orders or create one as a customer."""

    pagination_class = None

    def get_queryset(self):
        """Return orders where the user is customer or business."""
        user = self.request.user
        return Order.objects.filter(
            Q(customer_user=user) | Q(business_user=user)
        )

    def get_serializer_class(self):
        """Create serializer for POST, response serializer otherwise."""
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        """Any authenticated user lists; only customers create."""
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomerUser()]
        return [IsAuthenticated()]


class OrderStatusUpdateDeleteView(
    UpdateModelMixin, DestroyModelMixin, GenericAPIView
):
    """Update an order's status (owner) or delete it (staff)."""

    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    http_method_names = ["patch", "delete", "head", "options"]

    def get_permissions(self):
        """Assigned business user patches; staff deletes."""
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated(), IsAssignedBusinessUser()]

    def patch(self, request, *args, **kwargs):
        """Partially update the order's status."""
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Delete the order."""
        return self.destroy(request, *args, **kwargs)


class BaseOrderCountView(APIView):
    """Count a business user's orders in a fixed status."""

    permission_classes = [IsAuthenticated]
    status_value = None
    count_key = ""

    def get(self, request, business_user_id):
        """Return the count of matching orders for the user."""
        get_business_user_or_404(business_user_id)
        count = Order.objects.filter(
            business_user_id=business_user_id, status=self.status_value
        ).count()
        return Response({self.count_key: count})


class OrderCountView(BaseOrderCountView):
    """Count a business user's in-progress orders."""

    status_value = OrderStatus.IN_PROGRESS
    count_key = "order_count"


class CompletedOrderCountView(BaseOrderCountView):
    """Count a business user's completed orders."""

    status_value = OrderStatus.COMPLETED
    count_key = "completed_order_count"
