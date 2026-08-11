from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status, throttling
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.common.responses import success_response

from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    ForgotPasswordSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)
from .services import send_password_reset_email

User = get_user_model()


class AuthRateThrottle(throttling.AnonRateThrottle):
    scope = "auth"


@extend_schema(tags=["Auth"])
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return success_response(
            data={
                "user": UserSerializer(user, context={"request": request}).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            message="Registration successful.",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Auth"])
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return success_response(
            data={
                "user": data["user"],
                "tokens": {
                    "refresh": data["refresh"],
                    "access": data["access"],
                },
            },
            message="Login successful.",
        )


@extend_schema(tags=["Auth"])
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "message": "Refresh token is required.",
                    "errors": {"refresh": ["This field is required."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Invalid or expired refresh token.",
                    "errors": {"refresh": ["Token is invalid or already blacklisted."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return success_response(message="Logout successful.")


@extend_schema(tags=["Auth"])
class RefreshTokenView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != 200:
            return response
        return success_response(
            data={"tokens": response.data},
            message="Token refreshed.",
        )


@extend_schema(tags=["Auth"])
class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ProfileUpdateSerializer
        return UserSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, context={"request": request})
        return success_response(data=serializer.data, message="Profile retrieved.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(
            request.user, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=UserSerializer(request.user, context={"request": request}).data,
            message="Profile updated.",
        )


@extend_schema(tags=["Auth"])
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Password changed successfully.")


@extend_schema(tags=["Auth"])
class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]
    authentication_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # Always return a generic message to avoid email enumeration.
        generic = success_response(
            message=(
                "If an account exists for that email, password reset "
                "instructions have been sent."
            )
        )

        try:
            user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            return generic

        payload = send_password_reset_email(user, request=request)

        # Expose uid/token only in DEBUG to simplify local testing.
        from django.conf import settings

        if settings.DEBUG:
            return success_response(
                data={"debug_reset": payload},
                message=generic.data["message"],
            )
        return generic


@extend_schema(tags=["Auth"])
class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]
    authentication_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(message="Password has been reset successfully.")
