from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    STATUS_CHANGE = "status_change", "Status Change"
    EXPORT = "export", "Export"
    OTHER = "other", "Other"


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(
        max_length=32, choices=AuditAction.choices, db_index=True
    )
    module = models.CharField(max_length=64, blank=True, db_index=True)
    object_type = models.CharField(max_length=64, blank=True)
    object_id = models.CharField(max_length=64, blank=True, db_index=True)
    description = models.TextField(blank=True)
    method = models.CharField(max_length=16, blank=True)
    path = models.CharField(max_length=512, blank=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["module", "action", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} {self.module} @ {self.created_at}"
