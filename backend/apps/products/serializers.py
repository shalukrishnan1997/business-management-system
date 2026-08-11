from decimal import Decimal

from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "description",
            "status",
            "products_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "products_count")


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name", read_only=True, default=None
    )
    supplier_name = serializers.CharField(
        source="supplier.name", read_only=True, default=None
    )
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "product_code",
            "barcode",
            "name",
            "category",
            "category_name",
            "description",
            "purchase_price",
            "selling_price",
            "tax_percentage",
            "unit",
            "current_stock",
            "minimum_stock",
            "maximum_stock",
            "reorder_level",
            "is_low_stock",
            "supplier",
            "supplier_name",
            "product_image",
            "status",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "current_stock",
            "created_by",
            "created_at",
            "updated_at",
            "is_low_stock",
        )


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=64,
        help_text="Optional. Auto-generated as PRD-0001 if omitted.",
    )
    opening_stock = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        required=False,
        min_value=Decimal("0.000"),
        write_only=True,
        help_text="Initial stock on create only. Later changes use inventory module.",
    )

    class Meta:
        model = Product
        fields = (
            "product_code",
            "barcode",
            "name",
            "category",
            "description",
            "purchase_price",
            "selling_price",
            "tax_percentage",
            "unit",
            "minimum_stock",
            "maximum_stock",
            "reorder_level",
            "supplier",
            "product_image",
            "status",
            "opening_stock",
        )

    def validate_product_code(self, value):
        if not value:
            return value
        qs = Product.objects.filter(product_code__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Product code already exists.")
        return value.strip().upper()

    def validate_barcode(self, value):
        if not value:
            return value
        qs = Product.objects.filter(barcode__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Barcode already exists.")
        return value.strip()

    def validate_product_image(self, value):
        if value is None:
            return value
        max_size = 2 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Product image must be 2 MB or smaller.")
        content_type = getattr(value, "content_type", None)
        if content_type and content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise serializers.ValidationError("Only JPEG, PNG, or WebP images are allowed.")
        return value

    def validate(self, attrs):
        purchase = attrs.get(
            "purchase_price",
            getattr(self.instance, "purchase_price", None),
        )
        selling = attrs.get(
            "selling_price",
            getattr(self.instance, "selling_price", None),
        )
        # Soft warning via validation only if selling < purchase (allowed but flagged)
        # Keep allowed — many businesses sell at loss intentionally. No hard fail.
        _ = (purchase, selling)
        return attrs


class ProductPriceUpdateSerializer(serializers.Serializer):
    purchase_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, min_value=Decimal("0.00")
    )
    selling_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, min_value=Decimal("0.00")
    )
    tax_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, min_value=Decimal("0.00")
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Provide at least one price field.")
        return attrs
