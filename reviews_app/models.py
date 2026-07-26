"""Database models for business reviews."""

from django.contrib.auth.models import User
from django.db import models


class Review(models.Model):
    """A customer's review of a business user.

    Uniqueness of one review per (business_user, reviewer) pair is
    guaranteed by a database constraint, because the frontend only
    checks the reviews it has already loaded into memory.
    """

    business_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews_received"
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews_written"
    )
    rating = models.IntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Naming, newest-updated ordering and one review per pair."""

        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-updated_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["business_user", "reviewer"],
                name="unique_review_per_business_reviewer",
            )
        ]

    def __str__(self) -> str:
        """Return an identifying label for admin displays."""
        return f"Review #{self.pk} ({self.rating})"
