import django_filters

from .models import Payment, PaymentMethod, PaymentType


class PaymentFilter(django_filters.FilterSet):
    customer = django_filters.NumberFilter(field_name="customer_id")
    supplier = django_filters.NumberFilter(field_name="supplier_id")
    payment_type = django_filters.ChoiceFilter(choices=PaymentType.choices)
    payment_method = django_filters.ChoiceFilter(choices=PaymentMethod.choices)
    reference_type = django_filters.CharFilter(field_name="reference_type")
    reference_id = django_filters.NumberFilter(field_name="reference_id")
    date_from = django_filters.DateFilter(field_name="payment_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="payment_date", lookup_expr="lte")

    class Meta:
        model = Payment
        fields = [
            "customer",
            "supplier",
            "payment_type",
            "payment_method",
            "reference_type",
            "reference_id",
        ]
