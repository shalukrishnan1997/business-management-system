"""
Customer domain services — code generation and balances.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import Customer, CustomerStatus


def generate_customer_code() -> str:
    """Generate next code: CUS-0001, CUS-0002, ..."""
    latest = (
        Customer.objects.filter(customer_code__startswith="CUS-")
        .aggregate(Max("customer_code"))
        .get("customer_code__max")
    )
    if not latest:
        next_num = 1
    else:
        try:
            next_num = int(str(latest).split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            next_num = Customer.objects.count() + 1
    return f"CUS-{next_num:04d}"


@transaction.atomic
def create_customer(*, data: dict, user) -> Customer:
    payload = dict(data)
    raw_code = (payload.pop("customer_code", None) or "").strip()
    if raw_code:
        code = raw_code.upper()
    else:
        code = generate_customer_code()
        # Extremely unlikely race; bump until free.
        while Customer.objects.filter(customer_code=code).exists():
            try:
                n = int(code.split("-", 1)[1]) + 1
            except (IndexError, ValueError):
                n = Customer.objects.count() + 1
            code = f"CUS-{n:04d}"

    customer = Customer(customer_code=code, created_by=user, **payload)
    customer.save()
    return customer


def deactivate_customer(customer: Customer) -> Customer:
    customer.status = CustomerStatus.INACTIVE
    customer.save(update_fields=["status", "updated_at"])
    return customer


def activate_customer(customer: Customer) -> Customer:
    customer.status = CustomerStatus.ACTIVE
    customer.save(update_fields=["status", "updated_at"])
    return customer


def get_outstanding_balance(customer: Customer) -> Decimal:
    """
    Outstanding receivables:

    opening_balance
    + uninvoiced sale dues
    + open invoice balances
    − unallocated customer receipts (manual / not applied to an invoice)

    Invoice-applied payments already reduce invoice.balance (and linked sale dues).
    """
    uninvoiced_sale_due = Decimal("0.00")
    invoice_due = Decimal("0.00")
    unallocated_receipts = Decimal("0.00")
    try:
        from apps.sales.services import get_customer_uninvoiced_sale_due

        uninvoiced_sale_due = get_customer_uninvoiced_sale_due(customer)
    except Exception:
        uninvoiced_sale_due = Decimal("0.00")
    try:
        from apps.invoices.services import get_customer_invoice_balance

        invoice_due = get_customer_invoice_balance(customer)
    except Exception:
        invoice_due = Decimal("0.00")
    try:
        from apps.payments.services import get_customer_unallocated_receipts

        unallocated_receipts = get_customer_unallocated_receipts(customer)
    except Exception:
        unallocated_receipts = Decimal("0.00")

    return (
        customer.opening_balance
        + uninvoiced_sale_due
        + invoice_due
        - unallocated_receipts
    ).quantize(Decimal("0.01"))


def build_customer_statement(customer: Customer, *, date_from=None, date_to=None) -> dict:
    """Statement envelope. Extra line types added when finance modules exist."""
    outstanding = get_outstanding_balance(customer)
    debit = (
        customer.opening_balance if customer.opening_balance > 0 else Decimal("0.00")
    )
    credit = (
        -customer.opening_balance if customer.opening_balance < 0 else Decimal("0.00")
    )
    lines = [
        {
            "date": customer.created_at.date().isoformat(),
            "type": "opening_balance",
            "reference": customer.customer_code,
            "description": "Opening balance",
            "debit": str(debit),
            "credit": str(credit),
            "balance": str(customer.opening_balance),
        }
    ]
    return {
        "customer": {
            "id": customer.id,
            "customer_code": customer.customer_code,
            "name": customer.name,
            "company_name": customer.company_name,
            "email": customer.email,
            "phone": customer.phone,
        },
        "period": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
        },
        "opening_balance": str(customer.opening_balance),
        "outstanding_balance": str(outstanding),
        "credit_limit": str(customer.credit_limit),
        "generated_at": timezone.now().isoformat(),
        "lines": lines,
        "meta": {
            "sales_linked": True,
            "invoices_linked": True,
            "payments_linked": True,
            "note": (
                "Outstanding = opening + uninvoiced sale dues + invoice balances "
                "− unallocated receipts."
            ),
        },
    }


def get_sales_history(customer: Customer) -> list:
    from apps.sales.services import serialize_sale_history

    return serialize_sale_history(customer)


def get_invoice_history(customer: Customer) -> list:
    from apps.invoices.services import serialize_invoice_history

    return serialize_invoice_history(customer)


def get_payment_history(customer: Customer) -> list:
    from apps.payments.services import serialize_customer_payment_history

    return serialize_customer_payment_history(customer)
