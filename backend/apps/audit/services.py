"""
Audit logging — explicit service + optional API middleware.
"""
from .models import AuditAction, AuditLog


def log_audit(
    *,
    user=None,
    action: str = AuditAction.OTHER,
    module: str = "",
    object_type: str = "",
    object_id: str = "",
    description: str = "",
    method: str = "",
    path: str = "",
    status_code: int | None = None,
    ip_address: str | None = None,
    user_agent: str = "",
    metadata: dict | None = None,
) -> AuditLog:
    return AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        module=module or "",
        object_type=object_type or "",
        object_id=str(object_id) if object_id not in (None, "") else "",
        description=description or "",
        method=method or "",
        path=path or "",
        status_code=status_code,
        ip_address=ip_address,
        user_agent=(user_agent or "")[:512],
        metadata=metadata or {},
    )


def action_from_method(method: str) -> str:
    mapping = {
        "POST": AuditAction.CREATE,
        "PUT": AuditAction.UPDATE,
        "PATCH": AuditAction.UPDATE,
        "DELETE": AuditAction.DELETE,
    }
    return mapping.get((method or "").upper(), AuditAction.OTHER)


def module_from_path(path: str) -> str:
    """Best-effort module guess from /api/v1/<segment>/..."""
    parts = [p for p in (path or "").split("/") if p]
    if len(parts) >= 2 and parts[0] == "api" and parts[1] == "v1":
        segment = parts[2] if len(parts) > 2 else ""
    else:
        segment = parts[0] if parts else ""
    aliases = {
        "expense-categories": "expenses",
        "categories": "products",
        "departments": "employees",
        "designations": "employees",
        "auth": "users",
        "users": "users",
        "rbac": "users",
    }
    return aliases.get(segment, segment)


def get_client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
