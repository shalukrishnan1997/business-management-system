import django_filters

from .models import PaymentStatus, SalesOrder, SaleStatus


class SalesOrderFilter(django_filters.FilterSet):
    customer = django_filters.NumberFilter(field_name="customer_id")
    status = django_filters.ChoiceFilter(choices=SaleStatus.choices)
    payment_status = django_filters.ChoiceFilter(choices=PaymentStatus.choices)
    date_from = django_filters.DateFilter(field_name="sale_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="sale_date", lookup_expr="lte")

    class Meta:
        model = SalesOrder
        fields = ["customer", "status", "payment_status"]
