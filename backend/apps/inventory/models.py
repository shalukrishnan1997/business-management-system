from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import UserTrackedModel


class StockTransactionType(models.TextChoices):
    PURCHASE = "purchase", "Purchase"
    SALE = "sale", "Sale"
    SALE_RETURN = "sale_return", "Sale Return"
    PURCHASE_RETURN = "purchase_return", "Purchase Return"
    ADJUSTMENT_IN = "adjustment_in", "Adjustment In"
    ADJUSTMENT_OUT = "adjustment_out", "Adjustment Out"
    OPENING = "opening", "Opening Stock"


# Types that increase stock
STOCK_IN_TYPES = {
    StockTransactionType.PURCHASE,
    StockTransactionType.SALE_RETURN,
    StockTransactionType.ADJUSTMENT_IN,
    StockTransactionType.OPENING,
}

# Types that decrease stock
STOCK_OUT_TYPES = {
    StockTransactionType.SALE,
    StockTransactionType.PURCHASE_RETURN,
    StockTransactionType.ADJUSTMENT_OUT,
}


class StockTransaction(UserTrackedModel):
    """
    Immutable stock ledger row.

    Product.current_stock must only change through inventory services
    that create a StockTransaction.
    """

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="stock_transactions",
    )
    transaction_type = models.CharField(
        max_length=32,
        choices=StockTransactionType.choices,
        db_index=True,
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
        help_text="Always positive; direction comes from transaction_type.",
    )
    previous_stock = models.DecimalField(max_digits=12, decimal_places=3)
    new_stock = models.DecimalField(max_digits=12, decimal_places=3)
    reference_type = models.CharField(
        max_length=64,
        blank=True,
        help_text="e.g. purchase, sale, adjustment, opening",
    )
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["product", "-created_at"]),
            models.Index(fields=["transaction_type", "-created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="stock_txn_quantity_gt_0",
            ),
        ]

    def __str__(self):
        return (
            f"{self.transaction_type} {self.quantity} "
            f"on {self.product_id} ({self.previous_stock}→{self.new_stock})"
        )

    @property
    def is_inbound(self) -> bool:
        return self.transaction_type in STOCK_IN_TYPES


def allow_negative_stock() -> bool:
    """Company settings will override this later; env default for now."""
    return bool(getattr(settings, "ALLOW_NEGATIVE_STOCK", False))
