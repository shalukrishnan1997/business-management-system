from decimal import Decimal

from rest_framework import serializers

from apps.customers.models import Customer
from apps.products.models import Product
from apps.sales.models import SalesOrder

from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(
        source="product.product_code", read_only=True, default=None
    )

    class Meta:
        model = InvoiceItem
        fields = (
            "id",
            "product",
            "product_code",
            "description",
            "quantity",
            "unit_price",
            "discount",
            "tax",
            "total",
        )
        read_only_fields = ("id", "total", "product_code")


class InvoiceItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), required=False, allow_null=True
    )
    description = serializers.CharField(required=False, allow_blank=True, default="")
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


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_code = serializers.CharField(
        source="customer.customer_code", read_only=True
    )
    related_sale_number = serializers.CharField(
        source="related_sale.sale_number", read_only=True, default=None
    )
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )

    class Meta:
        model = Invoice
        fields = (
            "id",
            "invoice_number",
            "customer",
            "customer_code",
            "customer_name",
            "related_sale",
            "related_sale_number",
            "invoice_date",
            "due_date",
            "subtotal",
            "discount",
            "tax",
            "total",
            "paid_amount",
            "balance",
            "status",
            "notes",
            "items",
            "sent_at",
            "cancelled_at",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "invoice_number",
            "subtotal",
            "total",
            "balance",
            "status",
            "sent_at",
            "cancelled_at",
            "created_by",
            "created_at",
            "updated_at",
            "related_sale_number",
        )


class InvoiceCreateUpdateSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    related_sale = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrder.objects.all(), required=False, allow_null=True
    )
    invoice_date = serializers.DateField(required=False)
    due_date = serializers.DateField(required=False, allow_null=True)
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
    paid_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    items = InvoiceItemWriteSerializer(many=True, required=False)

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


class InvoiceFromSaleSerializer(serializers.Serializer):
    sale_id = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrder.objects.all(), source="sale"
    )
    due_days = serializers.IntegerField(required=False, default=30, min_value=0)


class InvoiceEmailSerializer(serializers.Serializer):
    to_email = serializers.EmailField(required=False, allow_blank=True)
