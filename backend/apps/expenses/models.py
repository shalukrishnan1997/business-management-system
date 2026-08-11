from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel, UserTrackedModel


class ExpenseCategoryStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class ExpenseStatus(models.TextChoices):
    RECORDED = "recorded", "Recorded"
    CANCELLED = "cancelled", "Cancelled"


class ExpensePaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    CARD = "card", "Card"
    UPI = "upi", "UPI"
    CHEQUE = "cheque", "Cheque"
    OTHER = "other", "Other"


class ExpenseCategory(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=ExpenseCategoryStatus.choices,
        default=ExpenseCategoryStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "expense categories"

    def __str__(self):
        return self.name


class Expense(UserTrackedModel):
    expense_number = models.CharField(max_length=32, unique=True, db_index=True)
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    expense_date = models.DateField(default=timezone.localdate, db_index=True)
    payment_method = models.CharField(
        max_length=32,
        choices=ExpensePaymentMethod.choices,
        default=ExpensePaymentMethod.CASH,
    )
    reference_number = models.CharField(
        max_length=128,
        blank=True,
        help_text="Vendor invoice / receipt / cheque number",
    )
    vendor_name = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=ExpenseStatus.choices,
        default=ExpenseStatus.RECORDED,
        db_index=True,
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-expense_date", "-id"]
        indexes = [
            models.Index(fields=["category", "expense_date"]),
            models.Index(fields=["status", "expense_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="expense_amount_gt_0",
            ),
        ]

    def __str__(self):
        return self.expense_number
