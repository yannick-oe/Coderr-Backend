"""API views for the base_info_app app."""

from django.db.models import Avg, Count
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import ProfileType, UserProfile
from offers_app.models import Offer
from reviews_app.models import Review


def collect_base_info():
    """Aggregate the four base-info metrics via the database."""
    reviews = Review.objects.aggregate(
        count=Count("id"), average=Avg("rating")
    )
    business_profiles = UserProfile.objects.filter(
        type=ProfileType.BUSINESS
    ).count()
    return {
        "review_count": reviews["count"],
        "average_rating": round(reviews["average"] or 0, 1),
        "business_profile_count": business_profiles,
        "offer_count": Offer.objects.count(),
    }


class BaseInfoView(APIView):
    """Public aggregate statistics for the landing page."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        """Return the platform's aggregate base information."""
        return Response(collect_base_info())
