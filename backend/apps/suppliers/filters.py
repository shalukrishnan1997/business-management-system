import django_filters

from .models import Supplier, SupplierStatus


class SupplierFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=SupplierStatus.choices)
    city = django_filters.CharFilter(lookup_expr="icontains")
    country = django_filters.CharFilter(lookup_expr="icontains")
    created_from = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    created_to = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )
    has_opening_balance = django_filters.BooleanFilter(
        method="filter_has_opening_balance"
    )

    class Meta:
        model = Supplier
        fields = ["status", "city", "country"]

    def filter_has_opening_balance(self, queryset, name, value):
        if value is True:
            return queryset.exclude(opening_balance=0)
        if value is False:
            return queryset.filter(opening_balance=0)
        return queryset
