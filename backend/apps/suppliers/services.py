"""
Supplier domain services — code generation, payables, statements.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import Supplier, SupplierStatus


def generate_supplier_code() -> str:
    """Generate next code: SUP-0001, SUP-0002, ..."""
    latest = (
        Supplier.objects.filter(supplier_code__startswith="SUP-")
        .aggregate(Max("supplier_code"))
        .get("supplier_code__max")
    )
    if not latest:
        next_num = 1
    else:
        try:
            next_num = int(str(latest).split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            next_num = Supplier.objects.count() + 1
    return f"SUP-{next_num:04d}"


@transaction.atomic
def create_supplier(*, data: dict, user) -> Supplier:
    payload = dict(data)
    raw_code = (payload.pop("supplier_code", None) or "").strip()
    if raw_code:
        code = raw_code.upper()
    else:
        code = generate_supplier_code()
        while Supplier.objects.filter(supplier_code=code).exists():
            try:
                n = int(code.split("-", 1)[1]) + 1
            except (IndexError, ValueError):
                n = Supplier.objects.count() + 1
            code = f"SUP-{n:04d}"

    supplier = Supplier(supplier_code=code, created_by=user, **payload)
    supplier.save()
    return supplier


def deactivate_supplier(supplier: Supplier) -> Supplier:
    supplier.status = SupplierStatus.INACTIVE
    supplier.save(update_fields=["status", "updated_at"])
    return supplier


def activate_supplier(supplier: Supplier) -> Supplier:
    supplier.status = SupplierStatus.ACTIVE
    supplier.save(update_fields=["status", "updated_at"])
    return supplier


def get_outstanding_balance(supplier: Supplier) -> Decimal:
    """
    Outstanding payables:

    opening_balance + purchase dues − unallocated supplier payments.

    Payments applied to purchases already reduce purchase.due_amount.
    """
    purchase_due = Decimal("0.00")
    unallocated_payments = Decimal("0.00")
    try:
        from apps.purchases.services import get_supplier_purchase_due

        purchase_due = get_supplier_purchase_due(supplier)
    except Exception:
        purchase_due = Decimal("0.00")
    try:
        from apps.payments.services import get_supplier_unallocated_payments

        unallocated_payments = get_supplier_unallocated_payments(supplier)
    except Exception:
        unallocated_payments = Decimal("0.00")

    return (
        supplier.opening_balance + purchase_due - unallocated_payments
    ).quantize(Decimal("0.01"))


def build_supplier_statement(supplier: Supplier, *, date_from=None, date_to=None) -> dict:
    outstanding = get_outstanding_balance(supplier)
    debit = (
        -supplier.opening_balance if supplier.opening_balance < 0 else Decimal("0.00")
    )
    credit = (
        supplier.opening_balance if supplier.opening_balance > 0 else Decimal("0.00")
    )
    lines = [
        {
            "date": supplier.created_at.date().isoformat(),
            "type": "opening_balance",
            "reference": supplier.supplier_code,
            "description": "Opening balance",
            "debit": str(debit),
            "credit": str(credit),
            "balance": str(supplier.opening_balance),
        }
    ]
    return {
        "supplier": {
            "id": supplier.id,
            "supplier_code": supplier.supplier_code,
            "name": supplier.name,
            "company_name": supplier.company_name,
            "email": supplier.email,
            "phone": supplier.phone,
        },
        "period": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
        },
        "opening_balance": str(supplier.opening_balance),
        "outstanding_balance": str(outstanding),
        "generated_at": timezone.now().isoformat(),
        "lines": lines,
        "meta": {
            "purchases_linked": True,
            "payments_linked": True,
            "note": (
                "Outstanding = opening + purchase dues − unallocated supplier payments."
            ),
        },
    }


def get_purchase_history(supplier: Supplier) -> list:
    from apps.purchases.services import serialize_purchase_history

    return serialize_purchase_history(supplier)


def get_payment_history(supplier: Supplier) -> list:
    from apps.payments.services import serialize_supplier_payment_history

    return serialize_supplier_payment_history(supplier)
