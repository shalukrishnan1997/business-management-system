from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.common.models import UserTrackedModel


class PaymentType(models.TextChoices):
    CUSTOMER_RECEIPT = "customer_receipt", "Customer Receipt"
    SUPPLIER_PAYMENT = "supplier_payment", "Supplier Payment"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    CARD = "card", "Card"
    UPI = "upi", "UPI"
    CHEQUE = "cheque", "Cheque"
    OTHER = "other", "Other"


class Payment(UserTrackedModel):
    payment_number = models.CharField(max_length=32, unique=True, db_index=True)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payments",
    )
    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payments",
    )
    payment_type = models.CharField(
        max_length=32, choices=PaymentType.choices, db_index=True
    )
    reference_type = models.CharField(
        max_length=32,
        blank=True,
        help_text="invoice | purchase | sale | manual",
    )
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    payment_method = models.CharField(
        max_length=32,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    transaction_reference = models.CharField(max_length=128, blank=True)
    payment_date = models.DateField(default=timezone.localdate, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-payment_date", "-id"]
        indexes = [
            models.Index(fields=["payment_type", "payment_date"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="payment_amount_gt_0",
            ),
        ]

    def __str__(self):
        return self.payment_number
