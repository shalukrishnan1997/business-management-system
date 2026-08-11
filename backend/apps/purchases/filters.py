import django_filters

from .models import PaymentStatus, Purchase, PurchaseStatus


class PurchaseFilter(django_filters.FilterSet):
    supplier = django_filters.NumberFilter(field_name="supplier_id")
    purchase_status = django_filters.ChoiceFilter(choices=PurchaseStatus.choices)
    payment_status = django_filters.ChoiceFilter(choices=PaymentStatus.choices)
    date_from = django_filters.DateFilter(field_name="purchase_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="purchase_date", lookup_expr="lte")

    class Meta:
        model = Purchase
        fields = ["supplier", "purchase_status", "payment_status"]
