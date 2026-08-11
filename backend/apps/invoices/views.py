from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action

from apps.common.permissions import CanManageInvoices, IsAuthenticatedAndActive
from apps.common.responses import success_response

from .filters import InvoiceFilter
from .models import Invoice
from .serializers import (
    InvoiceCreateUpdateSerializer,
    InvoiceEmailSerializer,
    InvoiceFromSaleSerializer,
    InvoiceSerializer,
)
from .services import (
    build_print_payload,
    cancel_invoice,
    create_invoice,
    create_invoice_from_sale,
    email_invoice,
    generate_invoice_pdf,
    mark_overdue_invoices,
    send_invoice,
    update_draft_invoice,
)


@extend_schema_view(
    list=extend_schema(tags=["Invoices"]),
    retrieve=extend_schema(tags=["Invoices"]),
    create=extend_schema(tags=["Invoices"]),
    update=extend_schema(tags=["Invoices"]),
    partial_update=extend_schema(tags=["Invoices"]),
    destroy=extend_schema(tags=["Invoices"]),
)
class InvoiceViewSet(viewsets.ModelViewSet):
    module = "invoices"
    permission_classes = [IsAuthenticatedAndActive, CanManageInvoices]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = InvoiceFilter
    search_fields = [
        "invoice_number",
        "customer__name",
        "customer__customer_code",
        "notes",
    ]
    ordering_fields = [
        "invoice_date",
        "due_date",
        "total",
        "balance",
        "created_at",
        "invoice_number",
    ]
    ordering = ["-invoice_date", "-id"]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        return Invoice.objects.select_related(
            "customer", "related_sale", "created_by"
        ).prefetch_related("items__product")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return InvoiceCreateUpdateSerializer
        return InvoiceSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = InvoiceSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        invoice = self.get_object()
        return success_response(
            data=InvoiceSerializer(invoice, context={"request": request}).data,
            message="Invoice retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "require_items": True}
        )
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        items = data.pop("items")
        invoice = create_invoice(data=data, items_data=items, user=request.user)
        invoice = self.get_queryset().get(pk=invoice.pk)
        return success_response(
            data=InvoiceSerializer(invoice, context={"request": request}).data,
            message="Invoice created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        invoice = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        items = data.pop("items", None)
        invoice = update_draft_invoice(
            invoice=invoice, data=data, items_data=items
        )
        invoice = self.get_queryset().get(pk=invoice.pk)
        return success_response(
            data=InvoiceSerializer(invoice, context={"request": request}).data,
            message="Invoice updated.",
        )

    @extend_schema(tags=["Invoices"])
    @action(detail=False, methods=["post"], url_path="from-sale")
    def from_sale(self, request):
        serializer = InvoiceFromSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.validated_data["sale"]
        due_days = serializer.validated_data.get("due_days", 30)
        invoice = create_invoice_from_sale(
            sale=sale, user=request.user, due_days=due_days
        )
        invoice = self.get_queryset().get(pk=invoice.pk)
        return success_response(
            data=InvoiceSerializer(invoice, context={"request": request}).data,
            message="Invoice created from sale.",
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["Invoices"])
    @action(detail=True, methods=["post"], url_path="send")
    def send(self, request, pk=None):
        invoice = send_invoice(self.get_object())
        return success_response(
            data=InvoiceSerializer(invoice, context={"request": request}).data,
            message="Invoice marked as sent.",
        )

    @extend_schema(tags=["Invoices"])
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        invoice = cancel_invoice(self.get_object())
        return success_response(
            data=InvoiceSerializer(invoice, context={"request": request}).data,
            message="Invoice cancelled.",
        )

    @extend_schema(tags=["Invoices"])
    @action(detail=False, methods=["post"], url_path="mark-overdue")
    def mark_overdue(self, request):
        updated = mark_overdue_invoices()
        return success_response(
            data={"updated": updated},
            message=f"Marked {updated} invoice(s) overdue.",
        )

    @extend_schema(tags=["Invoices"])
    @action(detail=True, methods=["get"], url_path="print", url_name="print")
    def print_invoice(self, request, pk=None):
        return success_response(
            data=build_print_payload(self.get_object()),
            message="Invoice print data.",
        )

    @extend_schema(tags=["Invoices"])
    @action(detail=True, methods=["get"], url_path="pdf", url_name="pdf")
    def pdf(self, request, pk=None):
        invoice = self.get_object()
        pdf_bytes = generate_invoice_pdf(invoice)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{invoice.invoice_number}.pdf"'
        )
        return response

    @extend_schema(tags=["Invoices"])
    @action(detail=True, methods=["post"], url_path="email")
    def email(self, request, pk=None):
        serializer = InvoiceEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        to_email = serializer.validated_data.get("to_email") or None
        result = email_invoice(invoice=self.get_object(), to_email=to_email or None)
        return success_response(data=result, message="Invoice emailed.")
