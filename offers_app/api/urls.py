"""URL routing for the offers_app API."""

from django.urls import path

from offers_app.api.views import (
    OfferDetailRetrieveView,
    OfferListCreateView,
    OfferRetrieveDestroyView,
)

urlpatterns = [
    path("offers/", OfferListCreateView.as_view(), name="offer-list-create"),
    path(
        "offers/<int:pk>/",
        OfferRetrieveDestroyView.as_view(),
        name="offer-detail",
    ),
    path(
        "offerdetails/<int:pk>/",
        OfferDetailRetrieveView.as_view(),
        name="offerdetail-detail",
    ),
]
