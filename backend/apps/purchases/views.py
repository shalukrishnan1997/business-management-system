from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action

from apps.common.permissions import CanManagePurchases, IsAuthenticatedAndActive
from apps.common.responses import success_response

from .filters import PurchaseFilter
from .models import Purchase
from .serializers import (
    PurchaseCreateUpdateSerializer,
    PurchaseSerializer,
)
from .services import (
    build_print_payload,
    cancel_purchase,
    create_purchase,
    mark_ordered,
    receive_purchase,
    update_draft_purchase,
)


@extend_schema_view(
    list=extend_schema(tags=["Purchases"]),
    retrieve=extend_schema(tags=["Purchases"]),
    create=extend_schema(tags=["Purchases"]),
    update=extend_schema(tags=["Purchases"]),
    partial_update=extend_schema(tags=["Purchases"]),
    destroy=extend_schema(tags=["Purchases"]),
)
class PurchaseViewSet(viewsets.ModelViewSet):
    """
    Purchase workflow:
    draft → ordered (optional) → received (stock in) / cancelled (reverse if received).
    """

    module = "purchases"
    permission_classes = [IsAuthenticatedAndActive, CanManagePurchases]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PurchaseFilter
    search_fields = ["purchase_number", "reference_number", "supplier__name", "notes"]
    ordering_fields = ["purchase_date", "grand_total", "created_at", "purchase_number"]
    ordering = ["-purchase_date", "-id"]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Purchase.objects.select_related(
            "supplier", "created_by"
        ).prefetch_related("items__product")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PurchaseCreateUpdateSerializer
        return PurchaseSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = PurchaseSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        purchase = self.get_object()
        return success_response(
            data=PurchaseSerializer(purchase, context={"request": request}).data,
            message="Purchase retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "require_items": True}
        )
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        items = data.pop("items")
        purchase = create_purchase(data=data, items_data=items, user=request.user)
        purchase = self.get_queryset().get(pk=purchase.pk)
        return success_response(
            data=PurchaseSerializer(purchase, context={"request": request}).data,
            message="Purchase created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        purchase = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        items = data.pop("items", None)
        purchase = update_draft_purchase(
            purchase=purchase, data=data, items_data=items
        )
        purchase = self.get_queryset().get(pk=purchase.pk)
        return success_response(
            data=PurchaseSerializer(purchase, context={"request": request}).data,
            message="Purchase updated.",
        )

    def destroy(self, request, *args, **kwargs):
        purchase = self.get_object()
        purchase = cancel_purchase(purchase=purchase, user=request.user)
        return success_response(
            data=PurchaseSerializer(purchase, context={"request": request}).data,
            message="Purchase cancelled.",
        )

    @extend_schema(tags=["Purchases"])
    @action(detail=True, methods=["post"], url_path="mark-ordered")
    def mark_ordered(self, request, pk=None):
        purchase = mark_ordered(self.get_object())
        purchase = self.get_queryset().get(pk=purchase.pk)
        return success_response(
            data=PurchaseSerializer(purchase, context={"request": request}).data,
            message="Purchase marked as ordered.",
        )

    @extend_schema(tags=["Purchases"])
    @action(detail=True, methods=["post"], url_path="receive")
    def receive(self, request, pk=None):
        purchase = receive_purchase(purchase=self.get_object(), user=request.user)
        purchase = self.get_queryset().get(pk=purchase.pk)
        return success_response(
            data=PurchaseSerializer(purchase, context={"request": request}).data,
            message="Purchase received. Stock updated.",
        )

    @extend_schema(tags=["Purchases"])
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        purchase = cancel_purchase(purchase=self.get_object(), user=request.user)
        purchase = self.get_queryset().get(pk=purchase.pk)
        return success_response(
            data=PurchaseSerializer(purchase, context={"request": request}).data,
            message="Purchase cancelled.",
        )

    @extend_schema(tags=["Purchases"])
    @action(detail=True, methods=["get"], url_path="print", url_name="print")
    def print_purchase(self, request, pk=None):
        payload = build_print_payload(self.get_object())
        return success_response(data=payload, message="Purchase order print data.")
