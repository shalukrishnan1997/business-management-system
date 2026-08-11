"""
Central RBAC matrix for Business Management System.

Convention:
- "read"  → SAFE_METHODS (GET, HEAD, OPTIONS)
- "write" → POST, PUT, PATCH, DELETE and custom mutating actions

Super Admin always bypasses checks in permission classes.
"""
from apps.accounts.models import UserRole as R

# Roles that can read / write each module.
MODULE_PERMISSIONS = {
    "users": {
        "read": {R.SUPER_ADMIN, R.ADMIN},
        "write": {R.SUPER_ADMIN, R.ADMIN},
    },
    "company": {
        "read": {R.SUPER_ADMIN, R.ADMIN, R.MANAGER, R.ACCOUNTANT, R.VIEWER},
        "write": {R.SUPER_ADMIN, R.ADMIN},
    },
    "customers": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.SALES_STAFF,
            R.INVENTORY_STAFF,
            R.VIEWER,
        },
        "write": {R.SUPER_ADMIN, R.ADMIN, R.MANAGER, R.SALES_STAFF},
    },
    "suppliers": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.SALES_STAFF,
            R.INVENTORY_STAFF,
            R.VIEWER,
        },
        "write": {R.SUPER_ADMIN, R.ADMIN, R.MANAGER, R.INVENTORY_STAFF},
    },
    "products": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.SALES_STAFF,
            R.INVENTORY_STAFF,
            R.VIEWER,
        },
        "write": {R.SUPER_ADMIN, R.ADMIN, R.MANAGER, R.INVENTORY_STAFF},
    },
    "inventory": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.INVENTORY_STAFF,
            R.VIEWER,
        },
        "write": {R.SUPER_ADMIN, R.ADMIN, R.INVENTORY_STAFF},
    },
    "purchases": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.INVENTORY_STAFF,
            R.VIEWER,
        },
        "write": {R.SUPER_ADMIN, R.ADMIN, R.MANAGER, R.INVENTORY_STAFF},
    },
    "sales": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.SALES_STAFF,
            R.INVENTORY_STAFF,
            R.VIEWER,
        },
        "write": {R.SUPER_ADMIN, R.ADMIN, R.MANAGER, R.SALES_STAFF},
    },
    "quotations": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.SALES_STAFF,
            R.VIEWER,
        },
        "write": {R.SUPER_ADMIN, R.ADMIN, R.MANAGER, R.SALES_STAFF},
    },
    "invoices": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.SALES_STAFF,
            R.VIEWER,
        },
        "write": {R.SUPER_ADMIN, R.ADMIN, R.ACCOUNTANT, R.SALES_STAFF},
    },
    "payments": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.SALES_STAFF,
            R.VIEWER,
        },
        "write": {R.SUPER_ADMIN, R.ADMIN, R.ACCOUNTANT, R.SALES_STAFF},
    },
    "expenses": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.VIEWER,
        },
        "write": {R.SUPER_ADMIN, R.ADMIN, R.ACCOUNTANT},
    },
    "employees": {
        "read": {R.SUPER_ADMIN, R.ADMIN, R.MANAGER, R.VIEWER},
        "write": {R.SUPER_ADMIN, R.ADMIN},
    },
    "reports": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.SALES_STAFF,
            R.INVENTORY_STAFF,
            R.VIEWER,
        },
        "write": {R.SUPER_ADMIN, R.ADMIN, R.ACCOUNTANT},
    },
    "dashboard": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.SALES_STAFF,
            R.INVENTORY_STAFF,
            R.VIEWER,
        },
        "write": set(),  # dashboard is read-only
    },
    "notifications": {
        "read": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.SALES_STAFF,
            R.INVENTORY_STAFF,
            R.VIEWER,
        },
        "write": {
            R.SUPER_ADMIN,
            R.ADMIN,
            R.MANAGER,
            R.ACCOUNTANT,
            R.SALES_STAFF,
            R.INVENTORY_STAFF,
            R.VIEWER,
        },
    },
    "audit": {
        "read": {R.SUPER_ADMIN, R.ADMIN},
        "write": set(),  # audit logs are append-only via services
    },
}

ADMIN_OR_ABOVE = {R.SUPER_ADMIN, R.ADMIN}


def role_can(role: str, module: str, action: str) -> bool:
    """
    action: "read" | "write"
    """
    if role == R.SUPER_ADMIN:
        return True
    perms = MODULE_PERMISSIONS.get(module)
    if not perms:
        return False
    return role in perms.get(action, set())


def effective_permissions_for_role(role: str) -> dict:
    """Return {module: {"read": bool, "write": bool}} for API/frontend."""
    result = {}
    for module in MODULE_PERMISSIONS:
        result[module] = {
            "read": role_can(role, module, "read"),
            "write": role_can(role, module, "write"),
        }
    return result
