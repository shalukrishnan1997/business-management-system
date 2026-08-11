"""
Inventory services — the only allowed path to change Product.current_stock.
"""
from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.products.models import Product

from .models import (
    STOCK_IN_TYPES,
    STOCK_OUT_TYPES,
    StockTransaction,
    StockTransactionType,
    allow_negative_stock,
)


def _as_qty(value) -> Decimal:
    qty = Decimal(str(value))
    if qty <= 0:
        raise ValidationError({"quantity": ["Quantity must be greater than zero."]})
    return qty.quantize(Decimal("0.001"))


@transaction.atomic
def apply_stock_movement(
    *,
    product: Product,
    transaction_type: str,
    quantity,
    user=None,
    reference_type: str = "",
    reference_id: int | None = None,
    remarks: str = "",
) -> StockTransaction:
    """
    Atomically update product stock and write a ledger row.

    Locks the product row (select_for_update) to avoid race conditions.
    """
    if transaction_type not in StockTransactionType.values:
        raise ValidationError(
            {"transaction_type": [f"Invalid transaction type: {transaction_type}"]}
        )

    qty = _as_qty(quantity)
    locked = Product.objects.select_for_update().get(pk=product.pk)
    previous = Decimal(locked.current_stock)

    if transaction_type in STOCK_IN_TYPES:
        new_stock = (previous + qty).quantize(Decimal("0.001"))
    elif transaction_type in STOCK_OUT_TYPES:
        new_stock = (previous - qty).quantize(Decimal("0.001"))
        if new_stock < 0 and not allow_negative_stock():
            raise ValidationError(
                {
                    "quantity": [
                        f"Only {previous} units available for {locked.product_code}."
                    ]
                }
            )
    else:
        raise ValidationError(
            {"transaction_type": ["Unsupported stock direction for this type."]}
        )

    locked.current_stock = new_stock
    locked.save(update_fields=["current_stock", "updated_at"])

    return StockTransaction.objects.create(
        product=locked,
        transaction_type=transaction_type,
        quantity=qty,
        previous_stock=previous,
        new_stock=new_stock,
        reference_type=reference_type or "",
        reference_id=reference_id,
        remarks=remarks or "",
        created_by=user,
    )


def adjust_stock_in(*, product, quantity, user=None, remarks: str = "") -> StockTransaction:
    return apply_stock_movement(
        product=product,
        transaction_type=StockTransactionType.ADJUSTMENT_IN,
        quantity=quantity,
        user=user,
        reference_type="adjustment",
        remarks=remarks or "Manual adjustment in",
    )


def adjust_stock_out(*, product, quantity, user=None, remarks: str = "") -> StockTransaction:
    return apply_stock_movement(
        product=product,
        transaction_type=StockTransactionType.ADJUSTMENT_OUT,
        quantity=quantity,
        user=user,
        reference_type="adjustment",
        remarks=remarks or "Manual adjustment out",
    )


def record_opening_stock(*, product, quantity, user=None) -> StockTransaction | None:
    """
    Apply opening stock via ledger.

    Expects product.current_stock to be 0 before calling.
    """
    qty = Decimal(str(quantity or 0))
    if qty <= 0:
        return None
    return apply_stock_movement(
        product=product,
        transaction_type=StockTransactionType.OPENING,
        quantity=qty,
        user=user,
        reference_type="opening",
        reference_id=product.pk,
        remarks="Opening stock",
    )


def get_product_stock_history(product: Product):
    return (
        StockTransaction.objects.filter(product=product)
        .select_related("created_by", "product")
        .all()
    )
