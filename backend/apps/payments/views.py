from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action

from apps.common.permissions import CanManagePayments, IsAuthenticatedAndActive
from apps.common.responses import success_response

from .filters import PaymentFilter
from .models import Payment
from .serializers import PaymentCreateSerializer, PaymentSerializer
from .services import build_payment_receipt, create_payment


@extend_schema_view(
    list=extend_schema(tags=["Payments"]),
    retrieve=extend_schema(tags=["Payments"]),
    create=extend_schema(tags=["Payments"]),
)
class PaymentViewSet(viewsets.ModelViewSet):
    module = "payments"
    permission_classes = [IsAuthenticatedAndActive, CanManagePayments]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PaymentFilter
    search_fields = [
        "payment_number",
        "transaction_reference",
        "customer__name",
        "supplier__name",
        "notes",
    ]
    ordering_fields = ["payment_date", "amount", "created_at", "payment_number"]
    ordering = ["-payment_date", "-id"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return Payment.objects.select_related(
            "customer", "supplier", "created_by"
        )

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        return PaymentSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = PaymentSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        payment = self.get_object()
        return success_response(
            data=PaymentSerializer(payment, context={"request": request}).data,
            message="Payment retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = create_payment(data=dict(serializer.validated_data), user=request.user)
        payment = self.get_queryset().get(pk=payment.pk)
        return success_response(
            data=PaymentSerializer(payment, context={"request": request}).data,
            message="Payment recorded.",
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["Payments"])
    @action(detail=True, methods=["get"], url_path="receipt")
    def receipt(self, request, pk=None):
        return success_response(
            data=build_payment_receipt(self.get_object()),
            message="Payment receipt.",
        )
