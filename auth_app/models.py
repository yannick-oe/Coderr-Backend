"""Database models for user accounts and profiles."""

from django.contrib.auth.models import User
from django.db import models

CHAR_FIELD_MAX_LENGTH = 255


class ProfileType(models.TextChoices):
    """Allowed account types for a user profile."""

    CUSTOMER = "customer", "Customer"
    BUSINESS = "business", "Business"


class UserProfile(models.Model):
    """Profile data owned by exactly one user account.

    The primary key is the related user's id, so ``profile/{pk}/``
    resolves a profile by user id. ``username``, ``email``,
    ``first_name`` and ``last_name`` live on ``User`` and are not
    duplicated here.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="profile",
    )
    file = models.ImageField(upload_to="profiles/", blank=True, null=True)
    location = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH, blank=True, default=""
    )
    tel = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH, blank=True, default=""
    )
    description = models.TextField(blank=True, default="")
    working_hours = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH, blank=True, default=""
    )
    type = models.CharField(
        max_length=CHAR_FIELD_MAX_LENGTH, choices=ProfileType.choices
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Human-readable naming and newest-first ordering."""

        verbose_name = "User profile"
        verbose_name_plural = "User profiles"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Return the username and account type for admin displays."""
        return f"{self.user.username} ({self.type})"
