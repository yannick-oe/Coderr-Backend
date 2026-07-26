"""Permission classes for the reviews_app API."""

from rest_framework.permissions import BasePermission

from auth_app.models import ProfileType, UserProfile
from reviews_app.models import Review


class IsReviewCustomer(BasePermission):
    """Allow only authenticated users with a customer profile."""

    def has_permission(self, request, view):
        """Return True when the user has a customer profile."""
        return UserProfile.objects.filter(
            user=request.user, type=ProfileType.CUSTOMER
        ).exists()


class HasNoExistingReview(BasePermission):
    """Reject a second review by the same reviewer of one business."""

    def has_permission(self, request, view):
        """Return True when no review by this reviewer exists yet."""
        return not self.duplicate_exists(request)

    def duplicate_exists(self, request):
        """Return True when the reviewer already reviewed the target."""
        try:
            business_id = int(request.data.get("business_user"))
        except (TypeError, ValueError):
            return False
        return Review.objects.filter(
            business_user_id=business_id, reviewer=request.user
        ).exists()


class IsReviewAuthor(BasePermission):
    """Allow only the review's author to modify or delete it."""

    def has_object_permission(self, request, view, obj):
        """Return True when the requester wrote the review."""
        return obj.reviewer_id == request.user.id
