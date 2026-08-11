from datetime import datetime

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action

from apps.common.permissions import CanManageCustomers, IsAuthenticatedAndActive
from apps.common.responses import success_response

from .filters import CustomerFilter
from .models import Customer
from .serializers import CustomerCreateUpdateSerializer, CustomerSerializer
from .services import (
    activate_customer,
    build_customer_statement,
    create_customer,
    deactivate_customer,
    get_invoice_history,
    get_outstanding_balance,
    get_payment_history,
    get_sales_history,
)


@extend_schema_view(
    list=extend_schema(tags=["Customers"]),
    retrieve=extend_schema(tags=["Customers"]),
    create=extend_schema(tags=["Customers"]),
    update=extend_schema(tags=["Customers"]),
    partial_update=extend_schema(tags=["Customers"]),
    destroy=extend_schema(tags=["Customers"]),
)
class CustomerViewSet(viewsets.ModelViewSet):
    """
    Customer CRUD with search, filters, and related actions.

    DELETE soft-deactivates (status=inactive).
    """

    module = "customers"
    permission_classes = [IsAuthenticatedAndActive, CanManageCustomers]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CustomerFilter
    search_fields = [
        "customer_code",
        "name",
        "company_name",
        "email",
        "phone",
        "tax_number",
        "city",
    ]
    ordering_fields = [
        "name",
        "customer_code",
        "created_at",
        "credit_limit",
        "opening_balance",
    ]
    ordering = ["name"]

    def get_queryset(self):
        return Customer.objects.select_related("created_by").all()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CustomerCreateUpdateSerializer
        return CustomerSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = CustomerSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        customer = self.get_object()
        return success_response(
            data=CustomerSerializer(customer, context={"request": request}).data,
            message="Customer retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = create_customer(data=serializer.validated_data, user=request.user)
        return success_response(
            data=CustomerSerializer(customer, context={"request": request}).data,
            message="Customer created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        customer = self.get_object()
        serializer = self.get_serializer(customer, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=CustomerSerializer(customer, context={"request": request}).data,
            message="Customer updated.",
        )

    def destroy(self, request, *args, **kwargs):
        customer = self.get_object()
        deactivate_customer(customer)
        return success_response(message="Customer deactivated.")

    @extend_schema(tags=["Customers"])
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        customer = activate_customer(self.get_object())
        return success_response(
            data=CustomerSerializer(customer, context={"request": request}).data,
            message="Customer activated.",
        )

    @extend_schema(tags=["Customers"])
    @action(detail=True, methods=["get"], url_path="outstanding")
    def outstanding(self, request, pk=None):
        customer = self.get_object()
        balance = get_outstanding_balance(customer)
        return success_response(
            data={
                "customer_id": customer.id,
                "customer_code": customer.customer_code,
                "opening_balance": str(customer.opening_balance),
                "outstanding_balance": str(balance),
                "credit_limit": str(customer.credit_limit),
                "available_credit": str(customer.credit_limit - balance)
                if customer.credit_limit is not None
                else None,
            },
            message="Outstanding balance retrieved.",
        )

    @extend_schema(tags=["Customers"])
    @action(detail=True, methods=["get"], url_path="statement")
    def statement(self, request, pk=None):
        customer = self.get_object()
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        parsed_from = (
            datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
        )
        parsed_to = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None
        data = build_customer_statement(
            customer, date_from=parsed_from, date_to=parsed_to
        )
        return success_response(data=data, message="Customer statement generated.")

    @extend_schema(tags=["Customers"])
    @action(detail=True, methods=["get"], url_path="sales-history")
    def sales_history(self, request, pk=None):
        customer = self.get_object()
        return success_response(
            data={
                "customer_id": customer.id,
                "results": get_sales_history(customer),
                "meta": {"linked": True, "note": "Sales linked."},
            },
            message="Customer sales history.",
        )

    @extend_schema(tags=["Customers"])
    @action(detail=True, methods=["get"], url_path="invoice-history")
    def invoice_history(self, request, pk=None):
        customer = self.get_object()
        return success_response(
            data={
                "customer_id": customer.id,
                "results": get_invoice_history(customer),
                "meta": {"linked": True, "note": "Invoices linked."},
            },
            message="Customer invoice history.",
        )

    @extend_schema(tags=["Customers"])
    @action(detail=True, methods=["get"], url_path="payment-history")
    def payment_history(self, request, pk=None):
        customer = self.get_object()
        return success_response(
            data={
                "customer_id": customer.id,
                "results": get_payment_history(customer),
                "meta": {"linked": True, "note": "Payments linked."},
            },
            message="Customer payment history.",
        )
