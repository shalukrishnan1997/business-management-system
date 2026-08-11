import django_filters

from .models import Invoice, InvoiceStatus


class InvoiceFilter(django_filters.FilterSet):
    customer = django_filters.NumberFilter(field_name="customer_id")
    status = django_filters.ChoiceFilter(choices=InvoiceStatus.choices)
    related_sale = django_filters.NumberFilter(field_name="related_sale_id")
    date_from = django_filters.DateFilter(field_name="invoice_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="invoice_date", lookup_expr="lte")
    due_from = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_to = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")
    overdue = django_filters.BooleanFilter(method="filter_overdue")

    class Meta:
        model = Invoice
        fields = ["customer", "status", "related_sale"]

    def filter_overdue(self, queryset, name, value):
        if value:
            return queryset.filter(status=InvoiceStatus.OVERDUE)
        return queryset
