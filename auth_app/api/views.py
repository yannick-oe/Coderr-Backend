"""API views for the auth_app app."""

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.serializers import (
    LoginSerializer,
    RegistrationSerializer,
)


def auth_response(user, token):
    """Return the token and user payload in the documented order."""
    return {
        "token": token.key,
        "username": user.username,
        "email": user.email,
        "user_id": user.pk,
    }


class RegistrationView(APIView):
    """Register a new user and return an auth token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Create the account and return 201 with the auth payload."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        data = auth_response(result["user"], result["token"])
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate a user and return a reused or new auth token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate credentials and return 200 with the auth payload."""
        serializer = LoginSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(auth_response(user, token))
