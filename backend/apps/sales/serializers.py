from decimal import Decimal

from rest_framework import serializers

from apps.customers.models import Customer
from apps.products.models import Product

from .models import SaleItem, SalesOrder


class SaleItemSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.product_code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SaleItem
        fields = (
            "id",
            "product",
            "product_code",
            "product_name",
            "quantity",
            "unit_price",
            "discount",
            "tax",
            "total",
        )
        read_only_fields = ("id", "total", "product_code", "product_name")


class SaleItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=Decimal("0.001")
    )
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.00")
    )
    tax = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )
    discount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )


class SalesOrderSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_code = serializers.CharField(
        source="customer.customer_code", read_only=True
    )
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )

    class Meta:
        model = SalesOrder
        fields = (
            "id",
            "sale_number",
            "customer",
            "customer_code",
            "customer_name",
            "sale_date",
            "subtotal",
            "discount",
            "tax",
            "shipping",
            "grand_total",
            "paid_amount",
            "due_amount",
            "payment_status",
            "status",
            "notes",
            "items",
            "completed_at",
            "cancelled_at",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "sale_number",
            "subtotal",
            "grand_total",
            "due_amount",
            "payment_status",
            "status",
            "completed_at",
            "cancelled_at",
            "created_by",
            "created_at",
            "updated_at",
        )


class SalesOrderCreateUpdateSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    sale_date = serializers.DateField(required=False)
    discount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )
    tax = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )
    shipping = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )
    paid_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    items = SaleItemWriteSerializer(many=True, required=False)

    def validate(self, attrs):
        if self.context.get("require_items", False) and not attrs.get("items"):
            raise serializers.ValidationError(
                {"items": ["At least one item is required."]}
            )
        if "items" in attrs and attrs["items"] is not None and len(attrs["items"]) == 0:
            raise serializers.ValidationError(
                {"items": ["At least one item is required."]}
            )
        return attrs
