"""Database models for customer orders."""

from django.contrib.auth.models import User
from django.db import models

from offers_app.models import OfferType

CHAR_FIELD_MAX_LENGTH = 255
PRICE_MAX_DIGITS = 10
PRICE_DECIMAL_PLACES = 2


class OrderStatus(models.TextChoices):
    """Allowed lifecycle states for an order."""

    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Order(models.Model):
    """A customer order snapshotting an offer detail at creation.

    The offer terms are copied here as plain fields, never linked by a
    foreign key, so the order survives the source offer being edited or
    deleted without mutating or cascade-deleting historical orders.
    """

    customer_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="customer_orders"
    )
    business_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="business_orders"
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
    status = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH,
        choices=OrderStatus.choices,
        default=OrderStatus.IN_PROGRESS,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Naming and deterministic newest-first ordering."""

        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        """Return an identifying label for admin displays."""
        return f"Order #{self.pk} ({self.status})"
