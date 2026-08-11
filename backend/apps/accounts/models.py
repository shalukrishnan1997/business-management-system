"""
Custom user model for Business Management System.

Design choices:
- Email is the login identifier (USERNAME_FIELD).
- Role lives on the user for simple RBAC (permission classes in Phase 5).
- Soft status field (active/inactive/suspended) instead of only is_active for clarity;
  is_active still gates authentication.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class UserRole(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super Admin"
    ADMIN = "admin", "Admin"
    MANAGER = "manager", "Manager"
    ACCOUNTANT = "accountant", "Accountant"
    SALES_STAFF = "sales_staff", "Sales Staff"
    INVENTORY_STAFF = "inventory_staff", "Inventory Staff"
    VIEWER = "viewer", "Viewer"


class UserStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    SUSPENDED = "suspended", "Suspended"


def user_profile_image_path(instance, filename):
    return f"profiles/user_{instance.pk or 'new'}/{filename}"


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email address", unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(
        upload_to=user_profile_image_path,
        blank=True,
        null=True,
    )
    role = models.CharField(
        max_length=32,
        choices=UserRole.choices,
        default=UserRole.VIEWER,
        db_index=True,
    )
    status = models.CharField(
        max_length=16,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
        db_index=True,
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can access the Django admin site.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to block authentication entirely.",
    )
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ["-date_joined"]
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email

    def sync_active_from_status(self):
        """Keep is_active aligned with business status."""
        self.is_active = self.status == UserStatus.ACTIVE

    def has_role(self, *roles) -> bool:
        return self.role in roles

    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN

    def is_admin_or_above(self) -> bool:
        return self.role in {UserRole.SUPER_ADMIN, UserRole.ADMIN}

    def can_read(self, module: str) -> bool:
        from apps.common.rbac import role_can

        return role_can(self.role, module, "read")

    def can_write(self, module: str) -> bool:
        from apps.common.rbac import role_can

        return role_can(self.role, module, "write")
