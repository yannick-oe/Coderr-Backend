"""URL routing for the auth_app API."""

from django.urls import path

from auth_app.api.views import LoginView, RegistrationView

urlpatterns = [
    path("registration/", RegistrationView.as_view(), name="registration"),
    path("login/", LoginView.as_view(), name="login"),
]
