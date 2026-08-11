from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.common.models import UserTrackedModel


class QuotationStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SENT = "sent", "Sent"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    EXPIRED = "expired", "Expired"


class Quotation(UserTrackedModel):
    quotation_number = models.CharField(max_length=32, unique=True, db_index=True)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="quotations",
    )
    quotation_date = models.DateField(default=timezone.localdate, db_index=True)
    valid_until = models.DateField(null=True, blank=True, db_index=True)
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    status = models.CharField(
        max_length=16,
        choices=QuotationStatus.choices,
        default=QuotationStatus.DRAFT,
        db_index=True,
    )
    notes = models.TextField(blank=True)
    converted_sale = models.ForeignKey(
        "sales.SalesOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_quotations",
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-quotation_date", "-id"]
        indexes = [
            models.Index(fields=["status", "quotation_date"]),
            models.Index(fields=["customer", "status"]),
        ]

    def __str__(self):
        return self.quotation_number

    @property
    def is_past_valid_until(self) -> bool:
        if not self.valid_until:
            return False
        return self.valid_until < timezone.localdate()


class QuotationItem(models.Model):
    quotation = models.ForeignKey(
        Quotation, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="quotation_items",
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        ordering = ["id"]

    def calculate_total(self) -> Decimal:
        return (
            (self.quantity * self.unit_price) - self.discount + self.tax
        ).quantize(Decimal("0.01"))
