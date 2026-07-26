"""Admin registrations for customer orders."""

from django.contrib import admin

from orders_app.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin listing for orders with status filtering."""

    list_display = (
        "id",
        "customer_user",
        "business_user",
        "status",
        "title",
        "created_at",
    )
    list_filter = ("status",)
    list_select_related = ("customer_user", "business_user")
