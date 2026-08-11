from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView

from apps.accounts.admin_serializers import (
    AdminUserCreateSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
)
from apps.accounts.models import UserRole
from apps.common.permissions import (
    CanManageCustomers,
    CanManageUsers,
    IsAuthenticatedAndActive,
)
from apps.common.rbac import MODULE_PERMISSIONS, effective_permissions_for_role
from apps.common.responses import success_response

User = get_user_model()


@extend_schema_view(
    list=extend_schema(tags=["Users"]),
    retrieve=extend_schema(tags=["Users"]),
    create=extend_schema(tags=["Users"]),
    update=extend_schema(tags=["Users"]),
    partial_update=extend_schema(tags=["Users"]),
    destroy=extend_schema(tags=["Users"]),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    Admin user management.

    Rules:
    - Admin / Super Admin only (via CanManageUsers)
    - Only Super Admin can create/assign Super Admin
    - Soft-deactivate preferred: DELETE sets status=inactive
    """

    module = "users"
    permission_classes = [IsAuthenticatedAndActive, CanManageUsers]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["role", "status", "is_active"]
    search_fields = ["email", "first_name", "last_name", "phone"]
    ordering_fields = ["date_joined", "email", "role"]
    ordering = ["-date_joined"]

    def get_queryset(self):
        qs = User.objects.all()
        # Admins should not manage Super Admin accounts in list/detail mutations
        if self.request.user.role != UserRole.SUPER_ADMIN:
            qs = qs.exclude(role=UserRole.SUPER_ADMIN)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return AdminUserCreateSerializer
        if self.action in ("update", "partial_update"):
            return AdminUserUpdateSerializer
        return AdminUserSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = AdminUserSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        return success_response(
            data=AdminUserSerializer(user, context={"request": request}).data,
            message="User retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return success_response(
            data=AdminUserSerializer(user, context={"request": request}).data,
            message="User created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=AdminUserSerializer(user, context={"request": request}).data,
            message="User updated.",
        )

    def destroy(self, request, *args, **kwargs):
        from apps.accounts.models import UserStatus
        from rest_framework.response import Response

        user = self.get_object()
        if user.pk == request.user.pk:
            return Response(
                {
                    "success": False,
                    "message": "You cannot deactivate your own account.",
                    "errors": {"detail": ["Self-deactivation is not allowed."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.status = UserStatus.INACTIVE
        user.sync_active_from_status()
        user.save(update_fields=["status", "is_active", "updated_at"])
        return success_response(message="User deactivated.")

    @extend_schema(tags=["Users"])
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        from apps.accounts.models import UserStatus

        user = self.get_object()
        user.status = UserStatus.ACTIVE
        user.sync_active_from_status()
        user.save(update_fields=["status", "is_active", "updated_at"])
        return success_response(
            data=AdminUserSerializer(user, context={"request": request}).data,
            message="User activated.",
        )


@extend_schema(tags=["RBAC"])
class MyPermissionsView(APIView):
    """
    Returns the authenticated user's effective module permissions.
    Used by the frontend to build menus and route guards.
    """

    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request):
        role = request.user.role
        return success_response(
            data={
                "role": role,
                "role_display": request.user.get_role_display(),
                "permissions": effective_permissions_for_role(role),
                "modules": sorted(MODULE_PERMISSIONS.keys()),
            },
            message="Permissions retrieved.",
        )


@extend_schema(tags=["RBAC"])
class CustomersPermissionDemoView(APIView):
    """
    Phase 5 demo endpoint: enforces the customers module matrix.

    GET  → roles with customers read
    POST → roles with customers write
    """

    module = "customers"
    permission_classes = [IsAuthenticatedAndActive, CanManageCustomers]

    def get(self, request):
        return success_response(
            data={
                "module": "customers",
                "action": "read",
                "role": request.user.role,
                "allowed": True,
            },
            message="Customers read access granted.",
        )

    def post(self, request):
        return success_response(
            data={
                "module": "customers",
                "action": "write",
                "role": request.user.role,
                "allowed": True,
            },
            message="Customers write access granted.",
        )
