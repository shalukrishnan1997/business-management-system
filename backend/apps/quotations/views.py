from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action

from apps.common.permissions import CanManageQuotations, IsAuthenticatedAndActive
from apps.common.responses import success_response
from apps.sales.models import SalesOrder
from apps.sales.serializers import SalesOrderSerializer

from .filters import QuotationFilter
from .models import Quotation
from .serializers import (
    QuotationCreateUpdateSerializer,
    QuotationEmailSerializer,
    QuotationSerializer,
)
from .services import (
    accept_quotation,
    build_print_payload,
    convert_quotation_to_sale,
    create_quotation,
    email_quotation,
    generate_quotation_pdf,
    maybe_mark_expired,
    reject_quotation,
    send_quotation,
    update_draft_quotation,
)


@extend_schema_view(
    list=extend_schema(tags=["Quotations"]),
    retrieve=extend_schema(tags=["Quotations"]),
    create=extend_schema(tags=["Quotations"]),
    update=extend_schema(tags=["Quotations"]),
    partial_update=extend_schema(tags=["Quotations"]),
    destroy=extend_schema(tags=["Quotations"]),
)
class QuotationViewSet(viewsets.ModelViewSet):
    module = "quotations"
    permission_classes = [IsAuthenticatedAndActive, CanManageQuotations]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = QuotationFilter
    search_fields = [
        "quotation_number",
        "customer__name",
        "customer__customer_code",
        "notes",
    ]
    ordering_fields = ["quotation_date", "grand_total", "created_at", "quotation_number"]
    ordering = ["-quotation_date", "-id"]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        return Quotation.objects.select_related(
            "customer", "created_by", "converted_sale"
        ).prefetch_related("items__product")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return QuotationCreateUpdateSerializer
        return QuotationSerializer

    def get_object(self):
        obj = super().get_object()
        return maybe_mark_expired(obj)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = QuotationSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        quotation = self.get_object()
        return success_response(
            data=QuotationSerializer(quotation, context={"request": request}).data,
            message="Quotation retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "require_items": True}
        )
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        items = data.pop("items")
        quotation = create_quotation(data=data, items_data=items, user=request.user)
        quotation = self.get_queryset().get(pk=quotation.pk)
        return success_response(
            data=QuotationSerializer(quotation, context={"request": request}).data,
            message="Quotation created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        quotation = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        items = data.pop("items", None)
        quotation = update_draft_quotation(
            quotation=quotation, data=data, items_data=items
        )
        quotation = self.get_queryset().get(pk=quotation.pk)
        return success_response(
            data=QuotationSerializer(quotation, context={"request": request}).data,
            message="Quotation updated.",
        )

    @extend_schema(tags=["Quotations"])
    @action(detail=True, methods=["post"], url_path="send")
    def send(self, request, pk=None):
        quotation = send_quotation(self.get_object())
        return success_response(
            data=QuotationSerializer(quotation, context={"request": request}).data,
            message="Quotation marked as sent.",
        )

    @extend_schema(tags=["Quotations"])
    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        quotation = accept_quotation(self.get_object())
        return success_response(
            data=QuotationSerializer(quotation, context={"request": request}).data,
            message="Quotation accepted.",
        )

    @extend_schema(tags=["Quotations"])
    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        quotation = reject_quotation(self.get_object())
        return success_response(
            data=QuotationSerializer(quotation, context={"request": request}).data,
            message="Quotation rejected.",
        )

    @extend_schema(tags=["Quotations"])
    @action(detail=True, methods=["post"], url_path="convert-to-sale")
    def convert_to_sale(self, request, pk=None):
        sale = convert_quotation_to_sale(quotation=self.get_object(), user=request.user)
        sale = (
            SalesOrder.objects.select_related("customer", "created_by")
            .prefetch_related("items__product")
            .get(pk=sale.pk)
        )
        quotation = self.get_queryset().get(pk=pk)
        return success_response(
            data={
                "quotation": QuotationSerializer(
                    quotation, context={"request": request}
                ).data,
                "sale": SalesOrderSerializer(sale, context={"request": request}).data,
            },
            message="Quotation converted to sale.",
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["Quotations"])
    @action(detail=True, methods=["get"], url_path="print", url_name="print")
    def print_quotation(self, request, pk=None):
        return success_response(
            data=build_print_payload(self.get_object()),
            message="Quotation print data.",
        )

    @extend_schema(tags=["Quotations"])
    @action(detail=True, methods=["get"], url_path="pdf", url_name="pdf")
    def pdf(self, request, pk=None):
        quotation = self.get_object()
        pdf_bytes = generate_quotation_pdf(quotation)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{quotation.quotation_number}.pdf"'
        )
        return response

    @extend_schema(tags=["Quotations"])
    @action(detail=True, methods=["post"], url_path="email")
    def email(self, request, pk=None):
        serializer = QuotationEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        to_email = serializer.validated_data.get("to_email") or None
        result = email_quotation(quotation=self.get_object(), to_email=to_email or None)
        return success_response(data=result, message="Quotation emailed.")
