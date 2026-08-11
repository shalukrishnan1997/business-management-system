from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action

from apps.common.permissions import CanManageSales, IsAuthenticatedAndActive
from apps.common.responses import success_response

from .filters import SalesOrderFilter
from .models import SalesOrder
from .serializers import SalesOrderCreateUpdateSerializer, SalesOrderSerializer
from .services import (
    build_print_payload,
    cancel_sale,
    complete_sale,
    confirm_sale,
    create_sale,
    update_draft_sale,
)


@extend_schema_view(
    list=extend_schema(tags=["Sales"]),
    retrieve=extend_schema(tags=["Sales"]),
    create=extend_schema(tags=["Sales"]),
    update=extend_schema(tags=["Sales"]),
    partial_update=extend_schema(tags=["Sales"]),
    destroy=extend_schema(tags=["Sales"]),
)
class SalesOrderViewSet(viewsets.ModelViewSet):
    """
    Sales workflow:
    draft → confirmed (optional) → completed (stock out) / cancelled (reverse if completed).
    """

    module = "sales"
    permission_classes = [IsAuthenticatedAndActive, CanManageSales]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SalesOrderFilter
    search_fields = ["sale_number", "customer__name", "customer__customer_code", "notes"]
    ordering_fields = ["sale_date", "grand_total", "created_at", "sale_number"]
    ordering = ["-sale_date", "-id"]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return SalesOrder.objects.select_related(
            "customer", "created_by"
        ).prefetch_related("items__product")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return SalesOrderCreateUpdateSerializer
        return SalesOrderSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = SalesOrderSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        sale = self.get_object()
        return success_response(
            data=SalesOrderSerializer(sale, context={"request": request}).data,
            message="Sale retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "require_items": True}
        )
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        items = data.pop("items")
        sale = create_sale(data=data, items_data=items, user=request.user)
        sale = self.get_queryset().get(pk=sale.pk)
        return success_response(
            data=SalesOrderSerializer(sale, context={"request": request}).data,
            message="Sale created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        sale = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        items = data.pop("items", None)
        sale = update_draft_sale(sale=sale, data=data, items_data=items)
        sale = self.get_queryset().get(pk=sale.pk)
        return success_response(
            data=SalesOrderSerializer(sale, context={"request": request}).data,
            message="Sale updated.",
        )

    def destroy(self, request, *args, **kwargs):
        sale = cancel_sale(sale=self.get_object(), user=request.user)
        return success_response(
            data=SalesOrderSerializer(sale, context={"request": request}).data,
            message="Sale cancelled.",
        )

    @extend_schema(tags=["Sales"])
    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        sale = confirm_sale(self.get_object())
        sale = self.get_queryset().get(pk=sale.pk)
        return success_response(
            data=SalesOrderSerializer(sale, context={"request": request}).data,
            message="Sale confirmed.",
        )

    @extend_schema(tags=["Sales"])
    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        sale = complete_sale(sale=self.get_object(), user=request.user)
        sale = self.get_queryset().get(pk=sale.pk)
        return success_response(
            data=SalesOrderSerializer(sale, context={"request": request}).data,
            message="Sale completed. Stock updated.",
        )

    @extend_schema(tags=["Sales"])
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        sale = cancel_sale(sale=self.get_object(), user=request.user)
        sale = self.get_queryset().get(pk=sale.pk)
        return success_response(
            data=SalesOrderSerializer(sale, context={"request": request}).data,
            message="Sale cancelled.",
        )

    @extend_schema(tags=["Sales"])
    @action(detail=True, methods=["get"], url_path="print", url_name="print")
    def print_sale(self, request, pk=None):
        payload = build_print_payload(self.get_object())
        return success_response(data=payload, message="Sale print data.")
