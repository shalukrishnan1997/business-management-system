from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "user",
        "action",
        "module",
        "method",
        "status_code",
        "path",
    )
    list_filter = ("action", "module", "method", "status_code")
    search_fields = ("description", "path", "object_id", "user__email")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
