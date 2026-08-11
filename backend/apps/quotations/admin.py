from django.contrib import admin

from .models import Quotation, QuotationItem


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0
    readonly_fields = ("total",)


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = (
        "quotation_number",
        "customer",
        "quotation_date",
        "valid_until",
        "grand_total",
        "status",
        "converted_sale",
    )
    list_filter = ("status", "quotation_date")
    search_fields = ("quotation_number", "customer__name", "customer__customer_code")
    inlines = [QuotationItemInline]
    readonly_fields = (
        "subtotal",
        "grand_total",
        "converted_sale",
        "sent_at",
        "accepted_at",
        "rejected_at",
        "created_at",
        "updated_at",
        "created_by",
    )
