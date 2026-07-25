"""Permission classes for the offers_app API."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from auth_app.models import ProfileType, UserProfile


class IsBusinessUser(BasePermission):
    """Allow only authenticated users with a business profile."""

    def has_permission(self, request, view):
        """Return True when the user has a business profile."""
        return UserProfile.objects.filter(
            user=request.user, type=ProfileType.BUSINESS
        ).exists()


class IsOfferOwnerOrReadOnly(BasePermission):
    """Allow reads to any user, writes only to the offer owner."""

    def has_object_permission(self, request, view, obj):
        """Permit safe methods; restrict writes to the owner."""
        if request.method in SAFE_METHODS:
            return True
        return obj.user_id == request.user.id
