import django_filters

from .models import AuditAction, AuditLog


class AuditLogFilter(django_filters.FilterSet):
    user = django_filters.NumberFilter(field_name="user_id")
    action = django_filters.ChoiceFilter(choices=AuditAction.choices)
    module = django_filters.CharFilter(field_name="module")
    object_id = django_filters.CharFilter(field_name="object_id")
    date_from = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    date_to = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )
    method = django_filters.CharFilter(field_name="method")
    status_code = django_filters.NumberFilter(field_name="status_code")

    class Meta:
        model = AuditLog
        fields = ["user", "action", "module", "object_id", "method", "status_code"]
