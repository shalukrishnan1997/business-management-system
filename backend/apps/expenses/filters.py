import django_filters

from .models import (
    Expense,
    ExpenseCategory,
    ExpenseCategoryStatus,
    ExpensePaymentMethod,
    ExpenseStatus,
)


class ExpenseCategoryFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=ExpenseCategoryStatus.choices)

    class Meta:
        model = ExpenseCategory
        fields = ["status"]


class ExpenseFilter(django_filters.FilterSet):
    category = django_filters.NumberFilter(field_name="category_id")
    status = django_filters.ChoiceFilter(choices=ExpenseStatus.choices)
    payment_method = django_filters.ChoiceFilter(choices=ExpensePaymentMethod.choices)
    date_from = django_filters.DateFilter(field_name="expense_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="expense_date", lookup_expr="lte")
    amount_min = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")

    class Meta:
        model = Expense
        fields = ["category", "status", "payment_method"]
