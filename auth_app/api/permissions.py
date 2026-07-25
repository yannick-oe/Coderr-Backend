"""Permission classes for the auth_app API."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProfileOwnerOrReadOnly(BasePermission):
    """Allow reads to any user, writes only to the profile owner."""

    def has_object_permission(self, request, view, obj):
        """Permit safe methods; restrict writes to the owner."""
        if request.method in SAFE_METHODS:
            return True
        return obj.user_id == request.user.id
