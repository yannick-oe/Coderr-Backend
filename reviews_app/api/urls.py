"""URL routing for the reviews_app API."""

from django.urls import path

from reviews_app.api.views import (
    ReviewListCreateView,
    ReviewUpdateDestroyView,
)

urlpatterns = [
    path(
        "reviews/",
        ReviewListCreateView.as_view(),
        name="review-list-create",
    ),
    path(
        "reviews/<int:pk>/",
        ReviewUpdateDestroyView.as_view(),
        name="review-detail",
    ),
]
