from decimal import Decimal

from rest_framework import serializers

from apps.products.models import Product

from .models import StockTransaction, StockTransactionType


class StockTransactionSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.product_code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )
    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )

    class Meta:
        model = StockTransaction
        fields = (
            "id",
            "product",
            "product_code",
            "product_name",
            "transaction_type",
            "transaction_type_display",
            "quantity",
            "previous_stock",
            "new_stock",
            "reference_type",
            "reference_id",
            "remarks",
            "created_by",
            "created_by_email",
            "created_at",
        )
        read_only_fields = fields


class StockAdjustmentSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=Decimal("0.001")
    )
    remarks = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Product not found.")
        return value
