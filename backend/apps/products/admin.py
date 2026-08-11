from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("name", "description")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_code",
        "name",
        "category",
        "selling_price",
        "purchase_price",
        "current_stock",
        "status",
        "supplier",
    )
    list_filter = ("status", "category", "unit")
    search_fields = ("product_code", "barcode", "name")
    readonly_fields = ("current_stock", "created_at", "updated_at", "created_by")
    raw_id_fields = ("supplier", "category")
