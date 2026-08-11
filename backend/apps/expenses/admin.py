from django.contrib import admin

from .models import Expense, ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "description")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "expense_number",
        "title",
        "category",
        "amount",
        "expense_date",
        "payment_method",
        "status",
    )
    list_filter = ("status", "payment_method", "expense_date", "category")
    search_fields = (
        "expense_number",
        "title",
        "vendor_name",
        "reference_number",
    )
    readonly_fields = (
        "expense_number",
        "cancelled_at",
        "created_at",
        "updated_at",
        "created_by",
    )
