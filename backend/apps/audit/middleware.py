"""
Append-only audit middleware for mutating /api/v1/ requests.
"""
from apps.audit.models import AuditAction
from apps.audit.services import (
    action_from_method,
    get_client_ip,
    log_audit,
    module_from_path,
)

SKIP_PREFIXES = (
    "/api/v1/health/",
    "/api/schema",
    "/api/docs",
    "/api/redoc",
)


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self._maybe_log(request, response)
        except Exception:
            # Never break the request because audit logging failed.
            pass
        return response

    def _maybe_log(self, request, response) -> None:
        path = request.path or ""
        if not path.startswith("/api/v1/"):
            return
        if any(path.startswith(p) for p in SKIP_PREFIXES):
            return
        method = (request.method or "").upper()
        if method in {"GET", "HEAD", "OPTIONS"}:
            return

        user = getattr(request, "user", None)
        module = module_from_path(path)
        action = action_from_method(method)
        if path.startswith("/api/v1/auth/login"):
            action = AuditAction.LOGIN
            module = "users"
        elif path.startswith("/api/v1/auth/logout"):
            action = AuditAction.LOGOUT
            module = "users"

        description = f"{method} {path} → {getattr(response, 'status_code', '')}"
        log_audit(
            user=user,
            action=action,
            module=module,
            description=description,
            method=method,
            path=path[:512],
            status_code=getattr(response, "status_code", None),
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
