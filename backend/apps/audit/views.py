from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets

from apps.common.permissions import CanAccessAudit, IsAuthenticatedAndActive
from apps.common.responses import success_response

from .filters import AuditLogFilter
from .models import AuditLog
from .serializers import AuditLogSerializer


@extend_schema_view(
    list=extend_schema(tags=["Audit"]),
    retrieve=extend_schema(tags=["Audit"]),
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    module = "audit"
    permission_classes = [IsAuthenticatedAndActive, CanAccessAudit]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AuditLogFilter
    search_fields = ["description", "path", "object_id", "module", "user__email"]
    ordering_fields = ["created_at", "action", "module", "status_code"]
    ordering = ["-created_at"]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        return AuditLog.objects.select_related("user")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(
            data=self.get_serializer(self.get_object()).data,
            message="Audit log retrieved.",
        )
