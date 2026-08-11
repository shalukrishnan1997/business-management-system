from rest_framework import serializers

from .models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )
    outstanding_balance = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = (
            "id",
            "supplier_code",
            "name",
            "company_name",
            "email",
            "phone",
            "tax_number",
            "address",
            "city",
            "country",
            "opening_balance",
            "outstanding_balance",
            "status",
            "notes",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "outstanding_balance",
        )

    def get_outstanding_balance(self, obj):
        from .services import get_outstanding_balance

        return str(get_outstanding_balance(obj))

    def validate_supplier_code(self, value):
        if not value:
            return value
        qs = Supplier.objects.filter(supplier_code__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Supplier code already exists.")
        return value.strip().upper()

    def validate_email(self, value):
        if value:
            return value.lower().strip()
        return value


class SupplierCreateUpdateSerializer(SupplierSerializer):
    supplier_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=32,
        help_text="Optional. Auto-generated as SUP-0001 if omitted.",
    )

    class Meta(SupplierSerializer.Meta):
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "outstanding_balance",
        )
