import django_filters
from django.db.models import F, Q

from .models import Category, CategoryStatus, Product, ProductStatus


class CategoryFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=CategoryStatus.choices)
    name = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Category
        fields = ["status", "name"]


class ProductFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=ProductStatus.choices)
    category = django_filters.NumberFilter(field_name="category_id")
    supplier = django_filters.NumberFilter(field_name="supplier_id")
    unit = django_filters.CharFilter(field_name="unit")
    low_stock = django_filters.BooleanFilter(method="filter_low_stock")
    price_min = django_filters.NumberFilter(field_name="selling_price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="selling_price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["status", "category", "supplier", "unit"]

    def filter_low_stock(self, queryset, name, value):
        if value is True:
            return queryset.filter(
                Q(reorder_level__gt=0, current_stock__lte=F("reorder_level"))
                | Q(reorder_level=0, current_stock__lte=F("minimum_stock"))
            )
        return queryset
