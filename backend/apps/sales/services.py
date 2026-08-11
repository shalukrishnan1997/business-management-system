"""
Sales workflow services.

Stock decreases only when a sale is completed.
Cancel after complete reverses stock via sale_return movements.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Max, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.inventory.models import StockTransactionType, allow_negative_stock
from apps.inventory.services import apply_stock_movement
from apps.products.models import Product, ProductStatus

from .models import PaymentStatus, SaleItem, SalesOrder, SaleStatus


def generate_sale_number() -> str:
    latest = (
        SalesOrder.objects.filter(sale_number__startswith="SAL-")
        .aggregate(Max("sale_number"))
        .get("sale_number__max")
    )
    if not latest:
        next_num = 1
    else:
        try:
            next_num = int(str(latest).split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            next_num = SalesOrder.objects.count() + 1
    return f"SAL-{next_num:04d}"


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


def recalculate_totals(sale: SalesOrder) -> SalesOrder:
    items = list(sale.items.all())
    subtotal = sum((i.quantity * i.unit_price for i in items), Decimal("0.00"))

    for item in items:
        item.total = item.calculate_total()
        item.save(update_fields=["total"])

    sale.subtotal = _money(subtotal)
    lines_net = sum((i.total for i in items), Decimal("0.00"))
    sale.grand_total = _money(lines_net - sale.discount + sale.tax + sale.shipping)
    if sale.paid_amount > sale.grand_total:
        sale.paid_amount = sale.grand_total
    sale.due_amount = _money(sale.grand_total - sale.paid_amount)
    sale.payment_status = derive_payment_status(
        grand_total=sale.grand_total, paid_amount=sale.paid_amount
    )
    sale.save(
        update_fields=[
            "subtotal",
            "grand_total",
            "paid_amount",
            "due_amount",
            "payment_status",
            "updated_at",
        ]
    )
    return sale


def _validate_product_for_sale(product: Product, quantity: Decimal) -> None:
    if product.status != ProductStatus.ACTIVE:
        raise ValidationError(
            {
                "items": [
                    f"Product {product.product_code} is inactive and cannot be sold."
                ]
            }
        )
    if quantity <= 0:
        raise ValidationError({"quantity": ["Quantity must be greater than zero."]})
    if not allow_negative_stock() and product.current_stock < quantity:
        raise ValidationError(
            {
                "quantity": [
                    f"Insufficient stock for {product.product_code}. "
                    f"Only {product.current_stock} available."
                ]
            }
        )


def _replace_items(sale: SalesOrder, items_data: list, *, validate_stock: bool = False) -> None:
    sale.items.all().delete()
    for row in items_data:
        product = row["product"]
        if isinstance(product, int):
            product = Product.objects.get(pk=product)
        quantity = _qty(row["quantity"])
        if validate_stock:
            _validate_product_for_sale(product, quantity)
        elif product.status != ProductStatus.ACTIVE:
            raise ValidationError(
                {
                    "items": [
                        f"Product {product.product_code} is inactive and cannot be sold."
                    ]
                }
            )
        item = SaleItem(
            sale=sale,
            product=product,
            quantity=quantity,
            unit_price=_money(row["unit_price"]),
            tax=_money(row.get("tax", 0)),
            discount=_money(row.get("discount", 0)),
        )
        item.total = item.calculate_total()
        item.save()


@transaction.atomic
def create_sale(*, data: dict, items_data: list, user) -> SalesOrder:
    if not items_data:
        raise ValidationError({"items": ["At least one sale item is required."]})

    number = data.get("sale_number") or generate_sale_number()
    while SalesOrder.objects.filter(sale_number=number).exists():
        number = generate_sale_number()

    sale = SalesOrder(
        sale_number=number,
        customer=data["customer"],
        sale_date=data.get("sale_date") or timezone.localdate(),
        discount=_money(data.get("discount", 0)),
        tax=_money(data.get("tax", 0)),
        shipping=_money(data.get("shipping", 0)),
        paid_amount=_money(data.get("paid_amount", 0)),
        notes=data.get("notes", ""),
        status=SaleStatus.DRAFT,
        created_by=user,
    )
    sale.save()
    # Draft may be saved without hard stock check; complete enforces stock.
    _replace_items(sale, items_data, validate_stock=False)
    return recalculate_totals(sale)


@transaction.atomic
def update_draft_sale(*, sale: SalesOrder, data: dict, items_data: list | None) -> SalesOrder:
    if sale.status not in {SaleStatus.DRAFT, SaleStatus.CONFIRMED}:
        raise ValidationError(
            {"detail": ["Only draft or confirmed sales can be edited."]}
        )

    for field in (
        "customer",
        "sale_date",
        "discount",
        "tax",
        "shipping",
        "paid_amount",
        "notes",
    ):
        if field in data:
            value = data[field]
            if field in {"discount", "tax", "shipping", "paid_amount"}:
                value = _money(value)
            setattr(sale, field, value)

    sale.save()
    if items_data is not None:
        if not items_data:
            raise ValidationError({"items": ["At least one sale item is required."]})
        _replace_items(sale, items_data, validate_stock=False)
    return recalculate_totals(sale)


@transaction.atomic
def confirm_sale(sale: SalesOrder) -> SalesOrder:
    if sale.status != SaleStatus.DRAFT:
        raise ValidationError({"detail": ["Only draft sales can be confirmed."]})
    if not sale.items.exists():
        raise ValidationError({"items": ["Add items before confirming."]})
    # Soft stock check on confirm (warn via error if insufficient)
    for item in sale.items.select_related("product"):
        _validate_product_for_sale(item.product, item.quantity)
    sale.status = SaleStatus.CONFIRMED
    sale.save(update_fields=["status", "updated_at"])
    return sale


@transaction.atomic
def complete_sale(*, sale: SalesOrder, user) -> SalesOrder:
    if sale.status == SaleStatus.COMPLETED:
        raise ValidationError({"detail": ["Sale is already completed."]})
    if sale.status == SaleStatus.CANCELLED:
        raise ValidationError({"detail": ["Cancelled sales cannot be completed."]})
    if not sale.items.exists():
        raise ValidationError({"items": ["Cannot complete a sale with no items."]})

    for item in sale.items.select_related("product"):
        _validate_product_for_sale(item.product, item.quantity)
        apply_stock_movement(
            product=item.product,
            transaction_type=StockTransactionType.SALE,
            quantity=item.quantity,
            user=user,
            reference_type="sale",
            reference_id=sale.pk,
            remarks=f"Sale completed {sale.sale_number}",
        )

    sale.status = SaleStatus.COMPLETED
    sale.completed_at = timezone.now()
    sale.save(update_fields=["status", "completed_at", "updated_at"])
    return sale


@transaction.atomic
def cancel_sale(*, sale: SalesOrder, user) -> SalesOrder:
    if sale.status == SaleStatus.CANCELLED:
        raise ValidationError({"detail": ["Sale is already cancelled."]})

    if sale.status == SaleStatus.COMPLETED:
        for item in sale.items.select_related("product"):
            apply_stock_movement(
                product=item.product,
                transaction_type=StockTransactionType.SALE_RETURN,
                quantity=item.quantity,
                user=user,
                reference_type="sale",
                reference_id=sale.pk,
                remarks=f"Sale cancelled {sale.sale_number}",
            )

    sale.status = SaleStatus.CANCELLED
    sale.cancelled_at = timezone.now()
    sale.save(update_fields=["status", "cancelled_at", "updated_at"])
    return sale


def get_customer_sale_due(customer) -> Decimal:
    total = (
        SalesOrder.objects.filter(customer=customer)
        .exclude(status=SaleStatus.CANCELLED)
        .aggregate(s=Sum("due_amount"))
        .get("s")
    )
    return _money(total or 0)


def get_customer_uninvoiced_sale_due(customer) -> Decimal:
    """
    Sale dues that are not yet covered by an active invoice.

    Once a sale has a non-cancelled invoice, outstanding uses invoice.balance
    instead so we do not double-count.
    """
    from apps.invoices.models import Invoice, InvoiceStatus

    invoiced_sale_ids = (
        Invoice.objects.filter(customer=customer, related_sale__isnull=False)
        .exclude(status=InvoiceStatus.CANCELLED)
        .values_list("related_sale_id", flat=True)
    )
    total = (
        SalesOrder.objects.filter(customer=customer)
        .exclude(status=SaleStatus.CANCELLED)
        .exclude(id__in=invoiced_sale_ids)
        .aggregate(s=Sum("due_amount"))
        .get("s")
    )
    return _money(total or 0)


def serialize_sale_history(customer) -> list:
    qs = (
        SalesOrder.objects.filter(customer=customer)
        .order_by("-sale_date", "-id")
        .values(
            "id",
            "sale_number",
            "sale_date",
            "grand_total",
            "paid_amount",
            "due_amount",
            "payment_status",
            "status",
        )
    )
    results = []
    for row in qs:
        row["sale_date"] = row["sale_date"].isoformat()
        row["grand_total"] = str(row["grand_total"])
        row["paid_amount"] = str(row["paid_amount"])
        row["due_amount"] = str(row["due_amount"])
        results.append(row)
    return results


def build_print_payload(sale: SalesOrder) -> dict:
    sale = (
        SalesOrder.objects.select_related("customer", "created_by")
        .prefetch_related("items__product")
        .get(pk=sale.pk)
    )
    return {
        "sale_number": sale.sale_number,
        "sale_date": sale.sale_date.isoformat(),
        "status": sale.status,
        "payment_status": sale.payment_status,
        "customer": {
            "code": sale.customer.customer_code,
            "name": sale.customer.name,
            "company_name": sale.customer.company_name,
            "email": sale.customer.email,
            "phone": sale.customer.phone,
            "address": sale.customer.address,
            "city": sale.customer.city,
            "country": sale.customer.country,
        },
        "totals": {
            "subtotal": str(sale.subtotal),
            "discount": str(sale.discount),
            "tax": str(sale.tax),
            "shipping": str(sale.shipping),
            "grand_total": str(sale.grand_total),
            "paid_amount": str(sale.paid_amount),
            "due_amount": str(sale.due_amount),
        },
        "notes": sale.notes,
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
            for item in sale.items.all()
        ],
        "created_by": getattr(sale.created_by, "email", None),
        "completed_at": sale.completed_at.isoformat() if sale.completed_at else None,
    }
