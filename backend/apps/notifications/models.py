from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class NotificationType(models.TextChoices):
    INFO = "info", "Info"
    SUCCESS = "success", "Success"
    WARNING = "warning", "Warning"
    DANGER = "danger", "Danger"
    SYSTEM = "system", "System"


class Notification(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    notification_type = models.CharField(
        max_length=16,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        db_index=True,
    )
    link = models.CharField(
        max_length=512,
        blank=True,
        help_text="Optional frontend path, e.g. /invoices/12",
    )
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    module = models.CharField(max_length=64, blank=True, db_index=True)
    object_id = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.title} → {self.user_id}"
