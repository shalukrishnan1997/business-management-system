from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import UserRole, UserStatus

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "profile_image",
            "role",
            "status",
            "is_active",
            "last_login",
            "date_joined",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "role",
            "status",
            "is_active",
            "last_login",
            "date_joined",
            "updated_at",
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone",
            "password",
            "password_confirm",
        )

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": ["Passwords do not match."]}
            )
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        # Public registration defaults to Viewer; admins change roles later.
        user = User.objects.create_user(
            password=password,
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE,
            **validated_data,
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login with email + password; embed role claims in the JWT."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        # Normalize email login
        field = self.username_field
        email = attrs.get(field, "")
        if email:
            attrs[field] = email.lower().strip()

        data = super().validate(attrs)

        if self.user.status != UserStatus.ACTIVE or not self.user.is_active:
            raise serializers.ValidationError(
                {"detail": "This account is inactive or suspended."}
            )

        data["user"] = UserSerializer(self.user, context=self.context).data
        return data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "profile_image")

    def validate_profile_image(self, value):
        if value is None:
            return value
        max_size = 2 * 1024 * 1024  # 2 MB
        if value.size > max_size:
            raise serializers.ValidationError("Profile image must be 2 MB or smaller.")
        valid_types = ("image/jpeg", "image/png", "image/webp")
        content_type = getattr(value, "content_type", None)
        if content_type and content_type not in valid_types:
            raise serializers.ValidationError(
                "Only JPEG, PNG, or WebP images are allowed."
            )
        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": ["Current password is incorrect."]}
            )
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": ["Passwords do not match."]}
            )
        validate_password(attrs["new_password"], user=user)
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": ["Passwords do not match."]}
            )

        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
            raise serializers.ValidationError(
                {"uid": ["Invalid password reset link."]}
            ) from exc

        if not token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError(
                {"token": ["Invalid or expired password reset token."]}
            )

        validate_password(attrs["new_password"], user=user)
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


def build_password_reset_payload(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = token_generator.make_token(user)
    return {"uid": uid, "token": token}
