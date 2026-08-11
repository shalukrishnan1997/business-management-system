"""
Reusable DRF permission classes.

Usage on a view/viewset:
    permission_classes = [IsAuthenticatedAndActive, HasModuleAccess]
    module = "customers"   # view attribute consumed by HasModuleAccess
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import UserRole, UserStatus
from apps.common.rbac import ADMIN_OR_ABOVE, role_can


def _active_authenticated(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and getattr(user, "status", None) == UserStatus.ACTIVE
    )


class IsAuthenticatedAndActive(BasePermission):
    message = "Authentication credentials were not provided or account is inactive."

    def has_permission(self, request, view):
        return _active_authenticated(request.user)


class IsSuperAdmin(BasePermission):
    message = "Super Admin role required."

    def has_permission(self, request, view):
        return (
            _active_authenticated(request.user)
            and request.user.role == UserRole.SUPER_ADMIN
        )


class IsAdminOrAbove(BasePermission):
    message = "Admin or Super Admin role required."

    def has_permission(self, request, view):
        return (
            _active_authenticated(request.user)
            and request.user.role in ADMIN_OR_ABOVE
        )


class HasRole(BasePermission):
    """
    Allow if user.role is in view.allowed_roles.

    Example:
        allowed_roles = [UserRole.MANAGER, UserRole.ADMIN]
    """

    message = "You do not have the required role for this action."

    def has_permission(self, request, view):
        if not _active_authenticated(request.user):
            return False
        if request.user.role == UserRole.SUPER_ADMIN:
            return True
        allowed = getattr(view, "allowed_roles", [])
        return request.user.role in allowed


class IsReadOnly(BasePermission):
    """Allow only safe HTTP methods."""

    message = "This endpoint is read-only."

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class HasModuleAccess(BasePermission):
    """
    Module-based RBAC using apps.common.rbac.MODULE_PERMISSIONS.

    Set on the view:
        module = "customers"

    Or subclass and set `module_name`.
    """

    message = "You do not have permission to access this module."
    module_name = None

    def get_module(self, view) -> str | None:
        return self.module_name or getattr(view, "module", None)

    def has_permission(self, request, view):
        if not _active_authenticated(request.user):
            return False

        module = self.get_module(view)
        if not module:
            return False

        action = "read" if request.method in SAFE_METHODS else "write"
        allowed = role_can(request.user.role, module, action)
        if not allowed:
            self.message = (
                f"Your role cannot {action} the '{module}' module."
            )
        return allowed


class CanManageUsers(HasModuleAccess):
    module_name = "users"


class CanManageCustomers(HasModuleAccess):
    module_name = "customers"


class CanManageSuppliers(HasModuleAccess):
    module_name = "suppliers"


class CanManageProducts(HasModuleAccess):
    module_name = "products"


class CanManageInventory(HasModuleAccess):
    module_name = "inventory"


class CanManagePurchases(HasModuleAccess):
    module_name = "purchases"


class CanManageSales(HasModuleAccess):
    module_name = "sales"


class CanManageQuotations(HasModuleAccess):
    module_name = "quotations"


class CanManageInvoices(HasModuleAccess):
    module_name = "invoices"


class CanManagePayments(HasModuleAccess):
    module_name = "payments"


class CanManageExpenses(HasModuleAccess):
    module_name = "expenses"


class CanManageEmployees(HasModuleAccess):
    module_name = "employees"


class CanAccessReports(HasModuleAccess):
    module_name = "reports"


class CanAccessDashboard(HasModuleAccess):
    module_name = "dashboard"


class CanAccessAudit(HasModuleAccess):
    module_name = "audit"


class CanAccessNotifications(HasModuleAccess):
    module_name = "notifications"
