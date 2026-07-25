"""Admin registrations for user accounts and profiles."""

from django.contrib import admin

from auth_app.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin listing and search for user profiles."""

    list_display = ("user", "type", "location", "tel", "created_at")
    list_filter = ("type",)
    search_fields = ("user__username",)
    list_select_related = ("user",)
