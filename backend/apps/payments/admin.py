from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "payment_number",
        "payment_type",
        "amount",
        "payment_method",
        "payment_date",
        "customer",
        "supplier",
        "reference_type",
        "reference_id",
    )
    list_filter = ("payment_type", "payment_method", "payment_date")
    search_fields = ("payment_number", "transaction_reference", "customer__name", "supplier__name")
    readonly_fields = ("created_at", "updated_at", "created_by")
