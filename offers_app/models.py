"""Database models for offers and offer details."""

from django.contrib.auth.models import User
from django.db import models

CHAR_FIELD_MAX_LENGTH = 255
PRICE_MAX_DIGITS = 10
PRICE_DECIMAL_PLACES = 2


class OfferType(models.TextChoices):
    """Allowed pricing tiers for an offer detail."""

    BASIC = "basic", "Basic"
    STANDARD = "standard", "Standard"
    PREMIUM = "premium", "Premium"


class Offer(models.Model):
    """A service offer created by a business user."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="offers"
    )
    title = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
    image = models.ImageField(upload_to="offers/", blank=True, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Human-readable naming and newest-first ordering."""

        verbose_name = "Offer"
        verbose_name_plural = "Offers"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return the offer title for admin displays."""
        return self.title


class OfferDetail(models.Model):
    """A single pricing tier belonging to an offer."""

    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name="details"
    )
    title = models.CharField(max_length=CHAR_FIELD_MAX_LENGTH)
    revisions = models.IntegerField()
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=PRICE_MAX_DIGITS, decimal_places=PRICE_DECIMAL_PLACES
    )
    features = models.JSONField(default=list)
    offer_type = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH, choices=OfferType.choices
    )

    class Meta:
        """Naming, price ordering and one tier type per offer."""

        verbose_name = "Offer detail"
        verbose_name_plural = "Offer details"
        ordering = ["price"]
        constraints = [
            models.UniqueConstraint(
                fields=["offer", "offer_type"],
                name="unique_offer_type_per_offer",
            )
        ]

    def __str__(self) -> str:
        """Return the offer title and tier for admin displays."""
        return f"{self.offer.title} ({self.offer_type})"
