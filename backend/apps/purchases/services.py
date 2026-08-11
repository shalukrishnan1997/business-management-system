"""
Purchase workflow services.

Stock increases only when a purchase is received.
Cancel after receive reverses stock via purchase_return movements.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Max, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.inventory.models import StockTransactionType
from apps.inventory.services import apply_stock_movement
from apps.products.models import Product

from .models import PaymentStatus, Purchase, PurchaseItem, PurchaseStatus


def generate_purchase_number() -> str:
    latest = (
        Purchase.objects.filter(purchase_number__startswith="PUR-")
        .aggregate(Max("purchase_number"))
        .get("purchase_number__max")
    )
    if not latest:
        next_num = 1
    else:
        try:
            next_num = int(str(latest).split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            next_num = Purchase.objects.count() + 1
    return f"PUR-{next_num:04d}"


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _qty(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"))


def derive_payment_status(*, grand_total: Decimal, paid_amount: Decimal) -> str:
    if paid_amount <= 0:
        return PaymentStatus.UNPAID
    if paid_amount >= grand_total:
        return PaymentStatus.PAID
    return PaymentStatus.PARTIAL


def recalculate_totals(purchase: Purchase) -> Purchase:
    items = list(purchase.items.all())
    subtotal = sum((i.quantity * i.unit_price for i in items), Decimal("0.00"))

    for item in items:
        item.total = item.calculate_total()
        item.save(update_fields=["total"])

    purchase.subtotal = _money(subtotal)
    lines_net = sum((i.total for i in items), Decimal("0.00"))
    # grand = sum(line totals) - header discount + header tax + shipping
    purchase.grand_total = _money(
        lines_net - purchase.discount + purchase.tax + purchase.shipping_charge
    )
    if purchase.paid_amount > purchase.grand_total:
        purchase.paid_amount = purchase.grand_total
    purchase.due_amount = _money(purchase.grand_total - purchase.paid_amount)
    purchase.payment_status = derive_payment_status(
        grand_total=purchase.grand_total, paid_amount=purchase.paid_amount
    )
    purchase.save(
        update_fields=[
            "subtotal",
            "grand_total",
            "paid_amount",
            "due_amount",
            "payment_status",
            "updated_at",
        ]
    )
    return purchase


def _replace_items(purchase: Purchase, items_data: list) -> None:
    purchase.items.all().delete()
    for row in items_data:
        product = row["product"]
        if isinstance(product, int):
            product = Product.objects.get(pk=product)
        item = PurchaseItem(
            purchase=purchase,
            product=product,
            quantity=_qty(row["quantity"]),
            unit_price=_money(row["unit_price"]),
            tax=_money(row.get("tax", 0)),
            discount=_money(row.get("discount", 0)),
        )
        item.total = item.calculate_total()
        item.save()


@transaction.atomic
def create_purchase(*, data: dict, items_data: list, user) -> Purchase:
    if not items_data:
        raise ValidationError({"items": ["At least one purchase item is required."]})

    number = data.get("purchase_number") or generate_purchase_number()
    while Purchase.objects.filter(purchase_number=number).exists():
        number = generate_purchase_number()

    purchase = Purchase(
        purchase_number=number,
        supplier=data["supplier"],
        purchase_date=data.get("purchase_date") or timezone.localdate(),
        reference_number=data.get("reference_number", ""),
        discount=_money(data.get("discount", 0)),
        tax=_money(data.get("tax", 0)),
        shipping_charge=_money(data.get("shipping_charge", 0)),
        paid_amount=_money(data.get("paid_amount", 0)),
        notes=data.get("notes", ""),
        purchase_status=PurchaseStatus.DRAFT,
        created_by=user,
    )
    purchase.save()
    _replace_items(purchase, items_data)
    return recalculate_totals(purchase)


@transaction.atomic
def update_draft_purchase(*, purchase: Purchase, data: dict, items_data: list | None) -> Purchase:
    if purchase.purchase_status not in {
        PurchaseStatus.DRAFT,
        PurchaseStatus.ORDERED,
    }:
        raise ValidationError(
            {"detail": ["Only draft or ordered purchases can be edited."]}
        )

    for field in (
        "supplier",
        "purchase_date",
        "reference_number",
        "discount",
        "tax",
        "shipping_charge",
        "paid_amount",
        "notes",
    ):
        if field in data:
            value = data[field]
            if field in {"discount", "tax", "shipping_charge", "paid_amount"}:
                value = _money(value)
            setattr(purchase, field, value)

    purchase.save()
    if items_data is not None:
        if not items_data:
            raise ValidationError({"items": ["At least one purchase item is required."]})
        _replace_items(purchase, items_data)
    return recalculate_totals(purchase)


@transaction.atomic
def mark_ordered(purchase: Purchase) -> Purchase:
    if purchase.purchase_status != PurchaseStatus.DRAFT:
        raise ValidationError({"detail": ["Only draft purchases can be marked ordered."]})
    if not purchase.items.exists():
        raise ValidationError({"items": ["Add items before ordering."]})
    purchase.purchase_status = PurchaseStatus.ORDERED
    purchase.save(update_fields=["purchase_status", "updated_at"])
    return purchase


@transaction.atomic
def receive_purchase(*, purchase: Purchase, user) -> Purchase:
    if purchase.purchase_status == PurchaseStatus.RECEIVED:
        raise ValidationError({"detail": ["Purchase is already received."]})
    if purchase.purchase_status == PurchaseStatus.CANCELLED:
        raise ValidationError({"detail": ["Cancelled purchases cannot be received."]})
    if not purchase.items.exists():
        raise ValidationError({"items": ["Cannot receive a purchase with no items."]})

    for item in purchase.items.select_related("product"):
        apply_stock_movement(
            product=item.product,
            transaction_type=StockTransactionType.PURCHASE,
            quantity=item.quantity,
            user=user,
            reference_type="purchase",
            reference_id=purchase.pk,
            remarks=f"Purchase received {purchase.purchase_number}",
        )

    purchase.purchase_status = PurchaseStatus.RECEIVED
    purchase.received_at = timezone.now()
    purchase.save(update_fields=["purchase_status", "received_at", "updated_at"])
    return purchase


@transaction.atomic
def cancel_purchase(*, purchase: Purchase, user) -> Purchase:
    if purchase.purchase_status == PurchaseStatus.CANCELLED:
        raise ValidationError({"detail": ["Purchase is already cancelled."]})

    if purchase.purchase_status == PurchaseStatus.RECEIVED:
        for item in purchase.items.select_related("product"):
            apply_stock_movement(
                product=item.product,
                transaction_type=StockTransactionType.PURCHASE_RETURN,
                quantity=item.quantity,
                user=user,
                reference_type="purchase",
                reference_id=purchase.pk,
                remarks=f"Purchase cancelled {purchase.purchase_number}",
            )

    purchase.purchase_status = PurchaseStatus.CANCELLED
    purchase.cancelled_at = timezone.now()
    purchase.save(update_fields=["purchase_status", "cancelled_at", "updated_at"])
    return purchase


def get_supplier_purchase_due(supplier) -> Decimal:
    """Sum due amounts for non-cancelled purchases (payables)."""
    total = (
        Purchase.objects.filter(supplier=supplier)
        .exclude(purchase_status=PurchaseStatus.CANCELLED)
        .aggregate(s=Sum("due_amount"))
        .get("s")
    )
    return _money(total or 0)


def serialize_purchase_history(supplier) -> list:
    qs = (
        Purchase.objects.filter(supplier=supplier)
        .order_by("-purchase_date", "-id")
        .values(
            "id",
            "purchase_number",
            "purchase_date",
            "grand_total",
            "paid_amount",
            "due_amount",
            "payment_status",
            "purchase_status",
        )
    )
    results = []
    for row in qs:
        row["purchase_date"] = row["purchase_date"].isoformat()
        row["grand_total"] = str(row["grand_total"])
        row["paid_amount"] = str(row["paid_amount"])
        row["due_amount"] = str(row["due_amount"])
        results.append(row)
    return results


def build_print_payload(purchase: Purchase) -> dict:
    purchase = Purchase.objects.select_related("supplier", "created_by").prefetch_related(
        "items__product"
    ).get(pk=purchase.pk)
    return {
        "purchase_number": purchase.purchase_number,
        "purchase_date": purchase.purchase_date.isoformat(),
        "reference_number": purchase.reference_number,
        "status": purchase.purchase_status,
        "payment_status": purchase.payment_status,
        "supplier": {
            "code": purchase.supplier.supplier_code,
            "name": purchase.supplier.name,
            "company_name": purchase.supplier.company_name,
            "email": purchase.supplier.email,
            "phone": purchase.supplier.phone,
            "address": purchase.supplier.address,
            "city": purchase.supplier.city,
            "country": purchase.supplier.country,
        },
        "totals": {
            "subtotal": str(purchase.subtotal),
            "discount": str(purchase.discount),
            "tax": str(purchase.tax),
            "shipping_charge": str(purchase.shipping_charge),
            "grand_total": str(purchase.grand_total),
            "paid_amount": str(purchase.paid_amount),
            "due_amount": str(purchase.due_amount),
        },
        "notes": purchase.notes,
        "items": [
            {
                "product_code": item.product.product_code,
                "product_name": item.product.name,
                "quantity": str(item.quantity),
                "unit_price": str(item.unit_price),
                "discount": str(item.discount),
                "tax": str(item.tax),
                "total": str(item.total),
            }
            for item in purchase.items.all()
        ],
        "created_by": getattr(purchase.created_by, "email", None),
        "received_at": purchase.received_at.isoformat() if purchase.received_at else None,
    }
