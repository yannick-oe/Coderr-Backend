"""URL routing for the auth_app API."""

from django.urls import path

from auth_app.api.views import (
    BusinessProfileListView,
    CustomerProfileListView,
    LoginView,
    ProfileDetailView,
    RegistrationView,
)

urlpatterns = [
    path("registration/", RegistrationView.as_view(), name="registration"),
    path("login/", LoginView.as_view(), name="login"),
    path(
        "profile/<int:pk>/",
        ProfileDetailView.as_view(),
        name="profile-detail",
    ),
    path(
        "profiles/business/",
        BusinessProfileListView.as_view(),
        name="profiles-business",
    ),
    path(
        "profiles/customer/",
        CustomerProfileListView.as_view(),
        name="profiles-customer",
    ),
]
