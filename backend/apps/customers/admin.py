from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "customer_code",
        "name",
        "company_name",
        "email",
        "phone",
        "city",
        "status",
        "credit_limit",
        "opening_balance",
        "created_at",
    )
    list_filter = ("status", "country", "state", "city")
    search_fields = (
        "customer_code",
        "name",
        "company_name",
        "email",
        "phone",
        "tax_number",
    )
    readonly_fields = ("created_at", "updated_at", "created_by")
    ordering = ("name",)
