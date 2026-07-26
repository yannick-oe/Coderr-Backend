"""Admin registrations for business reviews."""

from django.contrib import admin

from reviews_app.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin listing for reviews with rating filtering."""

    list_display = (
        "id",
        "business_user",
        "reviewer",
        "rating",
        "updated_at",
    )
    list_filter = ("rating",)
    list_select_related = ("business_user", "reviewer")
