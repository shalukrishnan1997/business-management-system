"""
Payment services — customer receipts and supplier payments.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Max, Q, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.invoices.models import Invoice
from apps.invoices.services import apply_amount_to_invoice
from apps.purchases.models import Purchase, PurchaseStatus
from apps.purchases.services import derive_payment_status as derive_purchase_payment_status

from .models import Payment, PaymentMethod, PaymentType


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def generate_payment_number() -> str:
    latest = (
        Payment.objects.filter(payment_number__startswith="PAY-")
        .aggregate(Max("payment_number"))
        .get("payment_number__max")
    )
    if not latest:
        next_num = 1
    else:
        try:
            next_num = int(str(latest).split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            next_num = Payment.objects.count() + 1
    return f"PAY-{next_num:04d}"


def get_customer_unallocated_receipts(customer) -> Decimal:
    """Receipts not applied to an invoice (already reflected in invoice.balance)."""
    total = (
        Payment.objects.filter(
            customer=customer, payment_type=PaymentType.CUSTOMER_RECEIPT
        )
        .filter(~Q(reference_type="invoice", reference_id__isnull=False))
        .aggregate(s=Sum("amount"))
        .get("s")
    )
    return _money(total or 0)


def get_supplier_unallocated_payments(supplier) -> Decimal:
    """Supplier payments not applied to a purchase (already in purchase.due)."""
    total = (
        Payment.objects.filter(
            supplier=supplier, payment_type=PaymentType.SUPPLIER_PAYMENT
        )
        .filter(~Q(reference_type="purchase", reference_id__isnull=False))
        .aggregate(s=Sum("amount"))
        .get("s")
    )
    return _money(total or 0)


@transaction.atomic
def apply_payment_to_purchase(*, purchase: Purchase, amount: Decimal) -> Purchase:
    amount = _money(amount)
    if purchase.purchase_status == PurchaseStatus.CANCELLED:
        raise ValidationError({"detail": ["Cannot pay a cancelled purchase."]})
    if amount > purchase.due_amount:
        raise ValidationError(
            {"amount": [f"Payment exceeds purchase due of {purchase.due_amount}."]}
        )
    purchase.paid_amount = _money(purchase.paid_amount + amount)
    purchase.due_amount = _money(purchase.grand_total - purchase.paid_amount)
    purchase.payment_status = derive_purchase_payment_status(
        grand_total=purchase.grand_total, paid_amount=purchase.paid_amount
    )
    purchase.save(
        update_fields=["paid_amount", "due_amount", "payment_status", "updated_at"]
    )
    return purchase


@transaction.atomic
def create_payment(*, data: dict, user) -> Payment:
    payment_type = data["payment_type"]
    amount = _money(data["amount"])
    if amount <= 0:
        raise ValidationError({"amount": ["Amount must be greater than zero."]})

    customer = data.get("customer")
    supplier = data.get("supplier")
    reference_type = (data.get("reference_type") or "").strip().lower()
    reference_id = data.get("reference_id")

    if payment_type == PaymentType.CUSTOMER_RECEIPT:
        if not customer:
            raise ValidationError({"customer": ["Customer is required for receipts."]})
        if supplier:
            raise ValidationError({"supplier": ["Do not set supplier on customer receipts."]})
    elif payment_type == PaymentType.SUPPLIER_PAYMENT:
        if not supplier:
            raise ValidationError({"supplier": ["Supplier is required for supplier payments."]})
        if customer:
            raise ValidationError({"customer": ["Do not set customer on supplier payments."]})
    else:
        raise ValidationError({"payment_type": ["Invalid payment type."]})

    number = generate_payment_number()
    while Payment.objects.filter(payment_number=number).exists():
        number = generate_payment_number()

    # Apply to document first (validates amounts)
    if reference_type == "invoice" and reference_id:
        if payment_type != PaymentType.CUSTOMER_RECEIPT:
            raise ValidationError({"reference_type": ["Invoices require customer receipts."]})
        try:
            invoice = Invoice.objects.select_for_update().get(pk=reference_id)
        except Invoice.DoesNotExist as exc:
            raise ValidationError({"reference_id": ["Invoice not found."]}) from exc
        if invoice.customer_id != customer.id:
            raise ValidationError({"customer": ["Invoice does not belong to this customer."]})
        apply_amount_to_invoice(invoice=invoice, amount=amount)
    elif reference_type == "purchase" and reference_id:
        if payment_type != PaymentType.SUPPLIER_PAYMENT:
            raise ValidationError(
                {"reference_type": ["Purchases require supplier payments."]}
            )
        try:
            purchase = Purchase.objects.select_for_update().get(pk=reference_id)
        except Purchase.DoesNotExist as exc:
            raise ValidationError({"reference_id": ["Purchase not found."]}) from exc
        if purchase.supplier_id != supplier.id:
            raise ValidationError({"supplier": ["Purchase does not belong to this supplier."]})
        apply_payment_to_purchase(purchase=purchase, amount=amount)
    elif reference_type and reference_type not in {"manual", ""}:
        raise ValidationError(
            {"reference_type": ["Supported references: invoice, purchase, manual."]}
        )

    payment = Payment.objects.create(
        payment_number=number,
        customer=customer,
        supplier=supplier,
        payment_type=payment_type,
        reference_type=reference_type or "manual",
        reference_id=reference_id,
        amount=amount,
        payment_method=data.get("payment_method") or PaymentMethod.CASH,
        transaction_reference=data.get("transaction_reference", ""),
        payment_date=data.get("payment_date") or timezone.localdate(),
        notes=data.get("notes", ""),
        created_by=user,
    )
    return payment


def serialize_customer_payment_history(customer) -> list:
    qs = (
        Payment.objects.filter(customer=customer)
        .order_by("-payment_date", "-id")
        .values(
            "id",
            "payment_number",
            "amount",
            "payment_method",
            "payment_date",
            "reference_type",
            "reference_id",
            "transaction_reference",
        )
    )
    results = []
    for row in qs:
        row["payment_date"] = row["payment_date"].isoformat()
        row["amount"] = str(row["amount"])
        results.append(row)
    return results


def serialize_supplier_payment_history(supplier) -> list:
    qs = (
        Payment.objects.filter(supplier=supplier)
        .order_by("-payment_date", "-id")
        .values(
            "id",
            "payment_number",
            "amount",
            "payment_method",
            "payment_date",
            "reference_type",
            "reference_id",
            "transaction_reference",
        )
    )
    results = []
    for row in qs:
        row["payment_date"] = row["payment_date"].isoformat()
        row["amount"] = str(row["amount"])
        results.append(row)
    return results


def build_payment_receipt(payment: Payment) -> dict:
    return {
        "payment_number": payment.payment_number,
        "payment_type": payment.payment_type,
        "payment_date": payment.payment_date.isoformat(),
        "amount": str(payment.amount),
        "payment_method": payment.payment_method,
        "transaction_reference": payment.transaction_reference,
        "customer": payment.customer.name if payment.customer else None,
        "supplier": payment.supplier.name if payment.supplier else None,
        "reference_type": payment.reference_type,
        "reference_id": payment.reference_id,
        "notes": payment.notes,
        "created_by": getattr(payment.created_by, "email", None),
    }
