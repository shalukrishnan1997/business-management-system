import django_filters

from .models import Quotation, QuotationStatus


class QuotationFilter(django_filters.FilterSet):
    customer = django_filters.NumberFilter(field_name="customer_id")
    status = django_filters.ChoiceFilter(choices=QuotationStatus.choices)
    date_from = django_filters.DateFilter(
        field_name="quotation_date", lookup_expr="gte"
    )
    date_to = django_filters.DateFilter(field_name="quotation_date", lookup_expr="lte")

    class Meta:
        model = Quotation
        fields = ["customer", "status"]
