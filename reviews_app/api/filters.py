"""Filter definitions for the reviews_app API."""

from django_filters import rest_framework as filters

from reviews_app.models import Review


class ReviewFilter(filters.FilterSet):
    """Filter reviews by business user and by author.

    Empty query values are treated as no filter, matching the offer
    list endpoint.
    """

    business_user_id = filters.NumberFilter(field_name="business_user_id")
    reviewer_id = filters.NumberFilter(field_name="reviewer_id")

    class Meta:
        """Bind the review filters to their query parameters."""

        model = Review
        fields = ["business_user_id", "reviewer_id"]
