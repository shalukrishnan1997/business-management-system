from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import UserRole, UserStatus
from apps.accounts.serializers import UserSerializer

User = get_user_model()


class AdminUserSerializer(UserSerializer):
    """Admin-facing user representation (includes role/status as writable via other serializers)."""

    class Meta(UserSerializer.Meta):
        read_only_fields = (
            "id",
            "last_login",
            "date_joined",
            "updated_at",
        )


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "status",
            "password",
            "password_confirm",
        )

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_role(self, value):
        request = self.context.get("request")
        if value == UserRole.SUPER_ADMIN and (
            not request
            or not request.user.is_authenticated
            or request.user.role != UserRole.SUPER_ADMIN
        ):
            raise serializers.ValidationError(
                "Only a Super Admin can assign the Super Admin role."
            )
        return value

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
        status_value = validated_data.get("status", UserStatus.ACTIVE)
        user = User.objects.create_user(password=password, **validated_data)
        user.status = status_value
        user.sync_active_from_status()
        if user.role == UserRole.SUPER_ADMIN:
            user.is_staff = True
            user.is_superuser = True
        user.save()
        return user


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone",
            "role",
            "status",
            "profile_image",
        )

    def validate_role(self, value):
        request = self.context.get("request")
        instance = self.instance

        if value == UserRole.SUPER_ADMIN and (
            not request
            or request.user.role != UserRole.SUPER_ADMIN
        ):
            raise serializers.ValidationError(
                "Only a Super Admin can assign the Super Admin role."
            )

        # Prevent Admin from editing a Super Admin account
        if (
            instance
            and instance.role == UserRole.SUPER_ADMIN
            and request
            and request.user.role != UserRole.SUPER_ADMIN
        ):
            raise serializers.ValidationError(
                "You cannot change a Super Admin account."
            )
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        instance = self.instance
        if (
            instance
            and instance.role == UserRole.SUPER_ADMIN
            and request
            and request.user.role != UserRole.SUPER_ADMIN
        ):
            raise serializers.ValidationError(
                "You cannot modify a Super Admin account."
            )
        return attrs

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if "status" in validated_data:
            instance.sync_active_from_status()
        if instance.role == UserRole.SUPER_ADMIN:
            instance.is_staff = True
            instance.is_superuser = True
        instance.save()
        return instance
