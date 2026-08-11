import django_filters

from .models import Customer, CustomerStatus


class CustomerFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=CustomerStatus.choices)
    city = django_filters.CharFilter(lookup_expr="icontains")
    state = django_filters.CharFilter(lookup_expr="icontains")
    country = django_filters.CharFilter(lookup_expr="icontains")
    created_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    credit_limit_min = django_filters.NumberFilter(
        field_name="credit_limit", lookup_expr="gte"
    )
    credit_limit_max = django_filters.NumberFilter(
        field_name="credit_limit", lookup_expr="lte"
    )
    has_opening_balance = django_filters.BooleanFilter(method="filter_has_opening_balance")

    class Meta:
        model = Customer
        fields = ["status", "city", "state", "country"]

    def filter_has_opening_balance(self, queryset, name, value):
        if value is True:
            return queryset.exclude(opening_balance=0)
        if value is False:
            return queryset.filter(opening_balance=0)
        return queryset
