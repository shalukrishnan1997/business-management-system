from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )
    outstanding_balance = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = (
            "id",
            "customer_code",
            "name",
            "company_name",
            "email",
            "phone",
            "alternate_phone",
            "tax_number",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "credit_limit",
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

    def validate_customer_code(self, value):
        if not value:
            return value
        qs = Customer.objects.filter(customer_code__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Customer code already exists.")
        return value.strip().upper()

    def validate_email(self, value):
        if value:
            return value.lower().strip()
        return value


class CustomerCreateUpdateSerializer(CustomerSerializer):
    customer_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=32,
        help_text="Optional. Auto-generated as CUS-0001 if omitted.",
    )

    class Meta(CustomerSerializer.Meta):
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "outstanding_balance",
        )
