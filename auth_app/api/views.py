"""API views for the auth_app app."""

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.permissions import IsProfileOwnerOrReadOnly
from auth_app.api.serializers import (
    BusinessProfileSerializer,
    CustomerProfileSerializer,
    LoginSerializer,
    ProfileDetailSerializer,
    RegistrationSerializer,
)
from auth_app.models import ProfileType, UserProfile


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

    authentication_classes = []
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

    authentication_classes = []
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


class ProfileDetailView(RetrieveUpdateAPIView):
    """Retrieve or partially update a single flat user profile."""

    queryset = UserProfile.objects.select_related("user")
    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated, IsProfileOwnerOrReadOnly]
    parser_classes = [MultiPartParser, JSONParser]
    http_method_names = ["get", "patch", "head", "options"]


class BusinessProfileListView(ListAPIView):
    """List every business profile as a bare array."""

    queryset = UserProfile.objects.select_related("user").filter(
        type=ProfileType.BUSINESS
    )
    serializer_class = BusinessProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class CustomerProfileListView(ListAPIView):
    """List every customer profile as a bare array."""

    queryset = UserProfile.objects.select_related("user").filter(
        type=ProfileType.CUSTOMER
    )
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
