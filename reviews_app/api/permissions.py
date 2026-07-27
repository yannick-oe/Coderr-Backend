"""Permission classes for the reviews_app API."""

from rest_framework.permissions import BasePermission

from auth_app.models import ProfileType, UserProfile


class IsReviewCustomer(BasePermission):
    """Allow only authenticated users with a customer profile."""

    def has_permission(self, request, view):
        """Return True when the user has a customer profile."""
        return UserProfile.objects.filter(
            user=request.user, type=ProfileType.CUSTOMER
        ).exists()


class IsReviewAuthor(BasePermission):
    """Allow only the review's author to modify or delete it."""

    def has_object_permission(self, request, view, obj):
        """Return True when the requester wrote the review."""
        return obj.reviewer_id == request.user.id
