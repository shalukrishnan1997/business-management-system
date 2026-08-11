from decimal import Decimal

from rest_framework import serializers

from apps.customers.models import Customer
from apps.suppliers.models import Supplier

from .models import Payment, PaymentMethod, PaymentType


class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name", read_only=True, default=None
    )
    supplier_name = serializers.CharField(
        source="supplier.name", read_only=True, default=None
    )
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "payment_number",
            "customer",
            "customer_name",
            "supplier",
            "supplier_name",
            "payment_type",
            "reference_type",
            "reference_id",
            "amount",
            "payment_method",
            "transaction_reference",
            "payment_date",
            "notes",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class PaymentCreateSerializer(serializers.Serializer):
    payment_type = serializers.ChoiceField(choices=PaymentType.choices)
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), required=False, allow_null=True
    )
    supplier = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(), required=False, allow_null=True
    )
    reference_type = serializers.CharField(required=False, allow_blank=True, default="")
    reference_id = serializers.IntegerField(required=False, allow_null=True)
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    payment_method = serializers.ChoiceField(
        choices=PaymentMethod.choices, required=False, default=PaymentMethod.CASH
    )
    transaction_reference = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    payment_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
