from decimal import Decimal

from rest_framework import serializers

from .models import (
    Expense,
    ExpenseCategory,
    ExpenseCategoryStatus,
    ExpensePaymentMethod,
)


class ExpenseCategorySerializer(serializers.ModelSerializer):
    expenses_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = ExpenseCategory
        fields = (
            "id",
            "name",
            "description",
            "status",
            "expenses_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "expenses_count")


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )

    class Meta:
        model = Expense
        fields = (
            "id",
            "expense_number",
            "category",
            "category_name",
            "title",
            "description",
            "amount",
            "expense_date",
            "payment_method",
            "reference_number",
            "vendor_name",
            "notes",
            "status",
            "cancelled_at",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "expense_number",
            "status",
            "cancelled_at",
            "created_by",
            "created_at",
            "updated_at",
            "category_name",
        )


class ExpenseCreateUpdateSerializer(serializers.Serializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=ExpenseCategory.objects.all()
    )
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    expense_date = serializers.DateField(required=False)
    payment_method = serializers.ChoiceField(
        choices=ExpensePaymentMethod.choices,
        required=False,
        default=ExpensePaymentMethod.CASH,
    )
    reference_number = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    vendor_name = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class ExpenseSummaryQuerySerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    category = serializers.IntegerField(required=False)
