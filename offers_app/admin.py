"""Admin registrations for offers and offer details."""

from django.contrib import admin

from offers_app.models import Offer, OfferDetail


class OfferDetailInline(admin.TabularInline):
    """Inline editor for an offer's pricing tiers."""

    model = OfferDetail
    extra = 0


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin listing for offers with inline details."""

    list_display = ("id", "title", "user", "created_at", "updated_at")
    list_select_related = ("user",)
    inlines = [OfferDetailInline]


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """Admin listing for individual offer details."""

    list_display = ("id", "offer", "offer_type", "price")
    list_select_related = ("offer",)
    list_filter = ("offer_type",)
