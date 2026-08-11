from datetime import datetime

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action

from apps.common.permissions import CanManageSuppliers, IsAuthenticatedAndActive
from apps.common.responses import success_response

from .filters import SupplierFilter
from .models import Supplier
from .serializers import SupplierCreateUpdateSerializer, SupplierSerializer
from .services import (
    activate_supplier,
    build_supplier_statement,
    create_supplier,
    deactivate_supplier,
    get_outstanding_balance,
    get_payment_history,
    get_purchase_history,
)


@extend_schema_view(
    list=extend_schema(tags=["Suppliers"]),
    retrieve=extend_schema(tags=["Suppliers"]),
    create=extend_schema(tags=["Suppliers"]),
    update=extend_schema(tags=["Suppliers"]),
    partial_update=extend_schema(tags=["Suppliers"]),
    destroy=extend_schema(tags=["Suppliers"]),
)
class SupplierViewSet(viewsets.ModelViewSet):
    """
    Supplier CRUD with search, filters, and related actions.

    DELETE soft-deactivates (status=inactive).
    """

    module = "suppliers"
    permission_classes = [IsAuthenticatedAndActive, CanManageSuppliers]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SupplierFilter
    search_fields = [
        "supplier_code",
        "name",
        "company_name",
        "email",
        "phone",
        "tax_number",
        "city",
    ]
    ordering_fields = ["name", "supplier_code", "created_at", "opening_balance"]
    ordering = ["name"]

    def get_queryset(self):
        return Supplier.objects.select_related("created_by").all()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return SupplierCreateUpdateSerializer
        return SupplierSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = SupplierSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        supplier = self.get_object()
        return success_response(
            data=SupplierSerializer(supplier, context={"request": request}).data,
            message="Supplier retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = create_supplier(data=serializer.validated_data, user=request.user)
        return success_response(
            data=SupplierSerializer(supplier, context={"request": request}).data,
            message="Supplier created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        supplier = self.get_object()
        serializer = self.get_serializer(supplier, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=SupplierSerializer(supplier, context={"request": request}).data,
            message="Supplier updated.",
        )

    def destroy(self, request, *args, **kwargs):
        supplier = self.get_object()
        deactivate_supplier(supplier)
        return success_response(message="Supplier deactivated.")

    @extend_schema(tags=["Suppliers"])
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        supplier = activate_supplier(self.get_object())
        return success_response(
            data=SupplierSerializer(supplier, context={"request": request}).data,
            message="Supplier activated.",
        )

    @extend_schema(tags=["Suppliers"])
    @action(detail=True, methods=["get"], url_path="outstanding")
    def outstanding(self, request, pk=None):
        supplier = self.get_object()
        balance = get_outstanding_balance(supplier)
        return success_response(
            data={
                "supplier_id": supplier.id,
                "supplier_code": supplier.supplier_code,
                "opening_balance": str(supplier.opening_balance),
                "outstanding_balance": str(balance),
            },
            message="Outstanding payable retrieved.",
        )

    @extend_schema(tags=["Suppliers"])
    @action(detail=True, methods=["get"], url_path="statement")
    def statement(self, request, pk=None):
        supplier = self.get_object()
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        parsed_from = (
            datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
        )
        parsed_to = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None
        data = build_supplier_statement(
            supplier, date_from=parsed_from, date_to=parsed_to
        )
        return success_response(data=data, message="Supplier statement generated.")

    @extend_schema(tags=["Suppliers"])
    @action(detail=True, methods=["get"], url_path="purchase-history")
    def purchase_history(self, request, pk=None):
        supplier = self.get_object()
        return success_response(
            data={
                "supplier_id": supplier.id,
                "results": get_purchase_history(supplier),
                "meta": {"linked": True, "note": "Purchases linked."},
            },
            message="Supplier purchase history.",
        )

    @extend_schema(tags=["Suppliers"])
    @action(detail=True, methods=["get"], url_path="payment-history")
    def payment_history(self, request, pk=None):
        supplier = self.get_object()
        return success_response(
            data={
                "supplier_id": supplier.id,
                "results": get_payment_history(supplier),
                "meta": {"linked": True, "note": "Payments linked."},
            },
            message="Supplier payment history.",
        )
