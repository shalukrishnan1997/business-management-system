from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "title",
        "notification_type",
        "is_read",
        "module",
        "created_at",
    )
    list_filter = ("notification_type", "is_read", "module")
    search_fields = ("title", "message", "user__email")
    readonly_fields = ("created_at", "updated_at", "read_at")
