import django_filters

from .models import StockTransaction, StockTransactionType


class StockTransactionFilter(django_filters.FilterSet):
    product = django_filters.NumberFilter(field_name="product_id")
    transaction_type = django_filters.ChoiceFilter(
        choices=StockTransactionType.choices
    )
    reference_type = django_filters.CharFilter(lookup_expr="iexact")
    created_from = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    created_to = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = StockTransaction
        fields = ["product", "transaction_type", "reference_type"]
