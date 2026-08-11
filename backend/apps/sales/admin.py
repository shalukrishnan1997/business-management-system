from django.contrib import admin

from .models import SaleItem, SalesOrder


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ("total",)


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = (
        "sale_number",
        "customer",
        "sale_date",
        "grand_total",
        "paid_amount",
        "due_amount",
        "payment_status",
        "status",
    )
    list_filter = ("status", "payment_status", "sale_date")
    search_fields = ("sale_number", "customer__name", "customer__customer_code")
    inlines = [SaleItemInline]
    readonly_fields = (
        "subtotal",
        "grand_total",
        "due_amount",
        "payment_status",
        "completed_at",
        "cancelled_at",
        "created_at",
        "updated_at",
        "created_by",
    )
