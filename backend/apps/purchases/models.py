from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.common.models import UserTrackedModel


class PurchaseStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ORDERED = "ordered", "Ordered"
    RECEIVED = "received", "Received"
    CANCELLED = "cancelled", "Cancelled"


class PaymentStatus(models.TextChoices):
    UNPAID = "unpaid", "Unpaid"
    PARTIAL = "partial", "Partially Paid"
    PAID = "paid", "Paid"


class Purchase(UserTrackedModel):
    purchase_number = models.CharField(max_length=32, unique=True, db_index=True)
    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.PROTECT,
        related_name="purchases",
    )
    purchase_date = models.DateField(default=timezone.localdate, db_index=True)
    reference_number = models.CharField(max_length=64, blank=True)
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Header-level discount (in addition to line discounts).",
    )
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Header-level tax (in addition to line tax).",
    )
    shipping_charge = models.DecimalField(
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
    purchase_status = models.CharField(
        max_length=16,
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.DRAFT,
        db_index=True,
    )
    notes = models.TextField(blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-purchase_date", "-id"]
        indexes = [
            models.Index(fields=["purchase_status", "purchase_date"]),
            models.Index(fields=["supplier", "purchase_status"]),
        ]

    def __str__(self):
        return self.purchase_number


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="purchase_items",
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
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    discount = models.DecimalField(
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
        return f"{self.purchase.purchase_number} — {self.product_id}"

    def calculate_total(self) -> Decimal:
        line = (self.quantity * self.unit_price) - self.discount + self.tax
        return line.quantize(Decimal("0.01"))
