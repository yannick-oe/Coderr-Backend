"""Permission classes for the orders_app API."""

from rest_framework.permissions import BasePermission

from auth_app.models import ProfileType, UserProfile


class IsCustomerUser(BasePermission):
    """Allow only authenticated users with a customer profile."""

    def has_permission(self, request, view):
        """Return True when the user has a customer profile."""
        return UserProfile.objects.filter(
            user=request.user, type=ProfileType.CUSTOMER
        ).exists()


class IsAssignedBusinessUser(BasePermission):
    """Allow only the business user assigned to the order."""

    def has_object_permission(self, request, view, obj):
        """Return True when the requester owns the order as business."""
        return obj.business_user_id == request.user.id
