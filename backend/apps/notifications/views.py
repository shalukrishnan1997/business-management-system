from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView

from apps.common.permissions import (
    CanAccessNotifications,
    IsAdminOrAbove,
    IsAuthenticatedAndActive,
)
from apps.common.responses import success_response

from .filters import NotificationFilter
from .models import Notification
from .serializers import MarkReadSerializer, NotificationSerializer
from .services import (
    delete_notification,
    mark_notifications_read,
    unread_count as get_unread_count,
)
from .tasks import check_low_stock_and_notify, mark_overdue_invoices_and_notify


@extend_schema_view(
    list=extend_schema(tags=["Notifications"]),
    retrieve=extend_schema(tags=["Notifications"]),
    destroy=extend_schema(tags=["Notifications"]),
)
class NotificationViewSet(viewsets.ModelViewSet):
    module = "notifications"
    permission_classes = [IsAuthenticatedAndActive, CanAccessNotifications]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NotificationFilter
    search_fields = ["title", "message", "module"]
    ordering_fields = ["created_at", "is_read"]
    ordering = ["-created_at"]
    http_method_names = ["get", "delete", "post", "head", "options"]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        from rest_framework.exceptions import MethodNotAllowed

        raise MethodNotAllowed("POST")

    def retrieve(self, request, *args, **kwargs):
        return success_response(
            data=self.get_serializer(self.get_object()).data,
            message="Notification retrieved.",
        )

    def destroy(self, request, *args, **kwargs):
        notification = self.get_object()
        delete_notification(user=request.user, notification=notification)
        return success_response(message="Notification deleted.")

    @extend_schema(tags=["Notifications"])
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        return success_response(
            data={"unread_count": get_unread_count(request.user)},
            message="Unread notification count.",
        )

    @extend_schema(tags=["Notifications"])
    @action(detail=False, methods=["post"], url_path="mark-read")
    def mark_read(self, request):
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data.get("ids")
        updated = mark_notifications_read(
            user=request.user, ids=ids if ids else None
        )
        return success_response(
            data={
                "updated": updated,
                "unread_count": get_unread_count(request.user),
            },
            message="Notifications marked as read.",
        )

    @extend_schema(tags=["Notifications"])
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = mark_notifications_read(user=request.user, ids=None)
        return success_response(
            data={"updated": updated, "unread_count": 0},
            message="All notifications marked as read.",
        )


class RunLowStockCheckView(APIView):
    permission_classes = [IsAuthenticatedAndActive, IsAdminOrAbove]

    @extend_schema(tags=["Notifications"])
    def post(self, request):
        result = check_low_stock_and_notify.delay()
        # Eager mode returns EagerResult with .get(); async returns AsyncResult.
        data = result.get() if hasattr(result, "get") else {"task_id": result.id}
        return success_response(
            data=data if isinstance(data, dict) else {"result": data},
            message="Low stock check queued/completed.",
            status=status.HTTP_200_OK,
        )


class RunOverdueCheckView(APIView):
    permission_classes = [IsAuthenticatedAndActive, IsAdminOrAbove]

    @extend_schema(tags=["Notifications"])
    def post(self, request):
        result = mark_overdue_invoices_and_notify.delay()
        data = result.get() if hasattr(result, "get") else {"task_id": result.id}
        return success_response(
            data=data if isinstance(data, dict) else {"result": data},
            message="Overdue invoice check queued/completed.",
            status=status.HTTP_200_OK,
        )
