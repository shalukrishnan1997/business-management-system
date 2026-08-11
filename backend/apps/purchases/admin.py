from django.contrib import admin

from .models import Purchase, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0
    readonly_fields = ("total",)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "purchase_number",
        "supplier",
        "purchase_date",
        "grand_total",
        "paid_amount",
        "due_amount",
        "payment_status",
        "purchase_status",
    )
    list_filter = ("purchase_status", "payment_status", "purchase_date")
    search_fields = ("purchase_number", "reference_number", "supplier__name")
    inlines = [PurchaseItemInline]
    readonly_fields = (
        "subtotal",
        "grand_total",
        "due_amount",
        "payment_status",
        "received_at",
        "cancelled_at",
        "created_at",
        "updated_at",
        "created_by",
    )
