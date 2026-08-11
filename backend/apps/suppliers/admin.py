from django.contrib import admin

from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "supplier_code",
        "name",
        "company_name",
        "email",
        "phone",
        "city",
        "country",
        "status",
        "opening_balance",
        "created_at",
    )
    list_filter = ("status", "country", "city")
    search_fields = (
        "supplier_code",
        "name",
        "company_name",
        "email",
        "phone",
        "tax_number",
    )
    readonly_fields = ("created_at", "updated_at", "created_by")
    ordering = ("name",)
