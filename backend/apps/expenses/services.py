"""
Expense services — numbers, create/update, cancel, summaries.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Max, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (
    Expense,
    ExpenseCategory,
    ExpenseCategoryStatus,
    ExpensePaymentMethod,
    ExpenseStatus,
)


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def generate_expense_number() -> str:
    latest = (
        Expense.objects.filter(expense_number__startswith="EXP-")
        .aggregate(Max("expense_number"))
        .get("expense_number__max")
    )
    if not latest:
        next_num = 1
    else:
        try:
            next_num = int(str(latest).split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            next_num = Expense.objects.count() + 1
    return f"EXP-{next_num:04d}"


def activate_category(category: ExpenseCategory) -> ExpenseCategory:
    category.status = ExpenseCategoryStatus.ACTIVE
    category.save(update_fields=["status", "updated_at"])
    return category


def deactivate_category(category: ExpenseCategory) -> ExpenseCategory:
    category.status = ExpenseCategoryStatus.INACTIVE
    category.save(update_fields=["status", "updated_at"])
    return category


@transaction.atomic
def create_expense(*, data: dict, user) -> Expense:
    category = data["category"]
    if category.status != ExpenseCategoryStatus.ACTIVE:
        raise ValidationError({"category": ["Category is inactive."]})

    amount = _money(data["amount"])
    if amount <= 0:
        raise ValidationError({"amount": ["Amount must be greater than zero."]})

    number = generate_expense_number()
    while Expense.objects.filter(expense_number=number).exists():
        number = generate_expense_number()

    expense = Expense.objects.create(
        expense_number=number,
        category=category,
        title=data["title"].strip(),
        description=data.get("description", ""),
        amount=amount,
        expense_date=data.get("expense_date") or timezone.localdate(),
        payment_method=data.get("payment_method") or ExpensePaymentMethod.CASH,
        reference_number=data.get("reference_number", ""),
        vendor_name=data.get("vendor_name", ""),
        notes=data.get("notes", ""),
        status=ExpenseStatus.RECORDED,
        created_by=user,
    )
    return expense


@transaction.atomic
def update_expense(*, expense: Expense, data: dict) -> Expense:
    if expense.status == ExpenseStatus.CANCELLED:
        raise ValidationError({"detail": ["Cancelled expenses cannot be edited."]})

    if "category" in data:
        category = data["category"]
        if category.status != ExpenseCategoryStatus.ACTIVE:
            raise ValidationError({"category": ["Category is inactive."]})
        expense.category = category

    for field in (
        "title",
        "description",
        "expense_date",
        "payment_method",
        "reference_number",
        "vendor_name",
        "notes",
    ):
        if field in data:
            value = data[field]
            if field == "title" and isinstance(value, str):
                value = value.strip()
            setattr(expense, field, value)

    if "amount" in data:
        amount = _money(data["amount"])
        if amount <= 0:
            raise ValidationError({"amount": ["Amount must be greater than zero."]})
        expense.amount = amount

    expense.save()
    return expense


@transaction.atomic
def cancel_expense(expense: Expense) -> Expense:
    if expense.status == ExpenseStatus.CANCELLED:
        raise ValidationError({"detail": ["Expense is already cancelled."]})
    expense.status = ExpenseStatus.CANCELLED
    expense.cancelled_at = timezone.now()
    expense.save(update_fields=["status", "cancelled_at", "updated_at"])
    return expense


def expense_summary(*, date_from=None, date_to=None, category_id=None) -> dict:
    """Totals for recorded expenses (cancelled excluded)."""
    qs = Expense.objects.filter(status=ExpenseStatus.RECORDED)
    if date_from:
        qs = qs.filter(expense_date__gte=date_from)
    if date_to:
        qs = qs.filter(expense_date__lte=date_to)
    if category_id:
        qs = qs.filter(category_id=category_id)

    totals = qs.aggregate(total_amount=Sum("amount"), count=Count("id"))
    by_category = list(
        qs.values("category_id", "category__name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )
    for row in by_category:
        row["total"] = str(_money(row["total"] or 0))
        row["category_name"] = row.pop("category__name")

    return {
        "period": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
        },
        "total_amount": str(_money(totals["total_amount"] or 0)),
        "count": totals["count"] or 0,
        "by_category": by_category,
    }
