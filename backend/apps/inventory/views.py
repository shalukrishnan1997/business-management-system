from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, mixins, status, viewsets
from rest_framework.views import APIView

from apps.common.permissions import CanManageInventory, IsAuthenticatedAndActive
from apps.common.responses import success_response
from apps.products.models import Product
from apps.products.services import low_stock_queryset
from apps.products.serializers import ProductSerializer

from .filters import StockTransactionFilter
from .models import StockTransaction
from .serializers import StockAdjustmentSerializer, StockTransactionSerializer
from .services import adjust_stock_in, adjust_stock_out


@extend_schema_view(
    list=extend_schema(tags=["Inventory"]),
    retrieve=extend_schema(tags=["Inventory"]),
)
class StockTransactionViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Read-only stock ledger. Mutations happen via adjustment endpoints / other modules."""

    module = "inventory"
    permission_classes = [IsAuthenticatedAndActive, CanManageInventory]
    serializer_class = StockTransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = StockTransactionFilter
    ordering_fields = ["created_at", "quantity", "id"]
    ordering = ["-created_at", "-id"]

    def get_queryset(self):
        return StockTransaction.objects.select_related(
            "product", "created_by"
        ).all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        txn = self.get_object()
        return success_response(
            data=self.get_serializer(txn).data,
            message="Stock transaction retrieved.",
        )


@extend_schema(tags=["Inventory"])
class StockAdjustInView(APIView):
    permission_classes = [IsAuthenticatedAndActive, CanManageInventory]

    def post(self, request):
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = Product.objects.get(pk=serializer.validated_data["product_id"])
        txn = adjust_stock_in(
            product=product,
            quantity=serializer.validated_data["quantity"],
            user=request.user,
            remarks=serializer.validated_data.get("remarks", ""),
        )
        product.refresh_from_db()
        return success_response(
            data={
                "transaction": StockTransactionSerializer(txn).data,
                "product": ProductSerializer(product, context={"request": request}).data,
                "low_stock": product.is_low_stock,
            },
            message="Stock increased.",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Inventory"])
class StockAdjustOutView(APIView):
    permission_classes = [IsAuthenticatedAndActive, CanManageInventory]

    def post(self, request):
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = Product.objects.get(pk=serializer.validated_data["product_id"])
        txn = adjust_stock_out(
            product=product,
            quantity=serializer.validated_data["quantity"],
            user=request.user,
            remarks=serializer.validated_data.get("remarks", ""),
        )
        product.refresh_from_db()
        return success_response(
            data={
                "transaction": StockTransactionSerializer(txn).data,
                "product": ProductSerializer(product, context={"request": request}).data,
                "low_stock": product.is_low_stock,
            },
            message="Stock decreased.",
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Inventory"])
class InventoryLowStockView(APIView):
    """Low-stock alert list for inventory staff dashboards."""

    permission_classes = [IsAuthenticatedAndActive, CanManageInventory]

    def get(self, request):
        qs = low_stock_queryset().select_related("category", "supplier")
        data = ProductSerializer(qs, many=True, context={"request": request}).data
        return success_response(
            data={"count": len(data), "results": data},
            message="Low stock products.",
        )
