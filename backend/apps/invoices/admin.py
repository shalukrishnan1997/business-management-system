from django.contrib import admin

from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ("total",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "customer",
        "invoice_date",
        "due_date",
        "total",
        "paid_amount",
        "balance",
        "status",
    )
    list_filter = ("status", "invoice_date")
    search_fields = ("invoice_number", "customer__name", "customer__customer_code")
    inlines = [InvoiceItemInline]
    readonly_fields = (
        "subtotal",
        "total",
        "balance",
        "sent_at",
        "cancelled_at",
        "created_at",
        "updated_at",
        "created_by",
    )
