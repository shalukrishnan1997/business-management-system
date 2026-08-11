from django.contrib import admin

from .models import StockTransaction


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "transaction_type",
        "quantity",
        "previous_stock",
        "new_stock",
        "reference_type",
        "reference_id",
        "created_by",
        "created_at",
    )
    list_filter = ("transaction_type", "reference_type")
    search_fields = ("product__product_code", "product__name", "remarks")
    readonly_fields = (
        "product",
        "transaction_type",
        "quantity",
        "previous_stock",
        "new_stock",
        "reference_type",
        "reference_id",
        "remarks",
        "created_by",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
