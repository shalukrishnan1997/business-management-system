from decimal import Decimal

from rest_framework import serializers

from apps.products.models import Product
from apps.suppliers.models import Supplier

from .models import Purchase, PurchaseItem


class PurchaseItemSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.product_code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = PurchaseItem
        fields = (
            "id",
            "product",
            "product_code",
            "product_name",
            "quantity",
            "unit_price",
            "tax",
            "discount",
            "total",
        )
        read_only_fields = ("id", "total", "product_code", "product_name")


class PurchaseItemWriteSerializer(serializers.Serializer):
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


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    supplier_code = serializers.CharField(source="supplier.supplier_code", read_only=True)
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )

    class Meta:
        model = Purchase
        fields = (
            "id",
            "purchase_number",
            "supplier",
            "supplier_code",
            "supplier_name",
            "purchase_date",
            "reference_number",
            "subtotal",
            "discount",
            "tax",
            "shipping_charge",
            "grand_total",
            "paid_amount",
            "due_amount",
            "payment_status",
            "purchase_status",
            "notes",
            "items",
            "received_at",
            "cancelled_at",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "purchase_number",
            "subtotal",
            "grand_total",
            "due_amount",
            "payment_status",
            "purchase_status",
            "received_at",
            "cancelled_at",
            "created_by",
            "created_at",
            "updated_at",
        )


class PurchaseCreateUpdateSerializer(serializers.Serializer):
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all())
    purchase_date = serializers.DateField(required=False)
    reference_number = serializers.CharField(required=False, allow_blank=True, default="")
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
    shipping_charge = serializers.DecimalField(
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
    items = PurchaseItemWriteSerializer(many=True, required=False)

    def validate(self, attrs):
        # Create must include items; update may omit to keep existing lines.
        if self.context.get("require_items", False) and not attrs.get("items"):
            raise serializers.ValidationError(
                {"items": ["At least one item is required."]}
            )
        if "items" in attrs and attrs["items"] is not None and len(attrs["items"]) == 0:
            raise serializers.ValidationError(
                {"items": ["At least one item is required."]}
            )
        return attrs
