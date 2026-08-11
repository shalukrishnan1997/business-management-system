from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.common.models import UserTrackedModel


class SaleStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    CONFIRMED = "confirmed", "Confirmed"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class PaymentStatus(models.TextChoices):
    UNPAID = "unpaid", "Unpaid"
    PARTIAL = "partial", "Partially Paid"
    PAID = "paid", "Paid"


class SalesOrder(UserTrackedModel):
    sale_number = models.CharField(max_length=32, unique=True, db_index=True)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="sales",
    )
    sale_date = models.DateField(default=timezone.localdate, db_index=True)
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
    shipping = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    due_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    payment_status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        db_index=True,
    )
    status = models.CharField(
        max_length=16,
        choices=SaleStatus.choices,
        default=SaleStatus.DRAFT,
        db_index=True,
    )
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-sale_date", "-id"]
        indexes = [
            models.Index(fields=["status", "sale_date"]),
            models.Index(fields=["customer", "status"]),
        ]
        verbose_name = "sales order"
        verbose_name_plural = "sales orders"

    def __str__(self):
        return self.sale_number


class SaleItem(models.Model):
    sale = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="sale_items",
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

    def __str__(self):
        return f"{self.sale.sale_number} — {self.product_id}"

    def calculate_total(self) -> Decimal:
        return (
            (self.quantity * self.unit_price) - self.discount + self.tax
        ).quantize(Decimal("0.01"))
