"""
Invoice services — create, send, cancel, overdue, PDF/email, from-sale.
"""
from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Max, Sum
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework.exceptions import ValidationError

from apps.products.models import Product
from apps.sales.models import SalesOrder
from apps.sales.services import derive_payment_status

from .models import Invoice, InvoiceItem, InvoiceStatus


def generate_invoice_number() -> str:
    latest = (
        Invoice.objects.filter(invoice_number__startswith="INV-")
        .aggregate(Max("invoice_number"))
        .get("invoice_number__max")
    )
    if not latest:
        next_num = 1
    else:
        try:
            next_num = int(str(latest).split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            next_num = Invoice.objects.count() + 1
    return f"INV-{next_num:04d}"


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _qty(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"))


def refresh_invoice_status(invoice: Invoice) -> Invoice:
    if invoice.status == InvoiceStatus.CANCELLED:
        return invoice

    if invoice.balance <= 0:
        invoice.status = InvoiceStatus.PAID
    elif invoice.paid_amount > 0:
        invoice.status = InvoiceStatus.PARTIALLY_PAID
        if (
            invoice.due_date
            and invoice.due_date < timezone.localdate()
            and invoice.balance > 0
        ):
            invoice.status = InvoiceStatus.OVERDUE
    else:
        if (
            invoice.status in {InvoiceStatus.SENT, InvoiceStatus.OVERDUE}
            and invoice.due_date
            and invoice.due_date < timezone.localdate()
        ):
            invoice.status = InvoiceStatus.OVERDUE
        elif invoice.status not in {InvoiceStatus.DRAFT, InvoiceStatus.SENT}:
            invoice.status = InvoiceStatus.SENT if invoice.sent_at else InvoiceStatus.DRAFT

    invoice.save(update_fields=["status", "updated_at"])
    return invoice


def recalculate_totals(invoice: Invoice) -> Invoice:
    items = list(invoice.items.all())
    subtotal = sum((i.quantity * i.unit_price for i in items), Decimal("0.00"))
    for item in items:
        item.total = item.calculate_total()
        item.save(update_fields=["total"])

    invoice.subtotal = _money(subtotal)
    lines_net = sum((i.total for i in items), Decimal("0.00"))
    invoice.total = _money(lines_net - invoice.discount + invoice.tax)
    if invoice.paid_amount > invoice.total:
        invoice.paid_amount = invoice.total
    invoice.balance = _money(invoice.total - invoice.paid_amount)
    if invoice.balance < 0:
        raise ValidationError({"balance": ["Invoice balance cannot be negative."]})
    invoice.save(
        update_fields=[
            "subtotal",
            "total",
            "paid_amount",
            "balance",
            "updated_at",
        ]
    )
    return refresh_invoice_status(invoice)


def _replace_items(invoice: Invoice, items_data: list) -> None:
    invoice.items.all().delete()
    for row in items_data:
        product = row.get("product")
        if isinstance(product, int):
            product = Product.objects.get(pk=product)
        item = InvoiceItem(
            invoice=invoice,
            product=product,
            description=row.get("description")
            or (product.name if product else ""),
            quantity=_qty(row["quantity"]),
            unit_price=_money(row["unit_price"]),
            tax=_money(row.get("tax", 0)),
            discount=_money(row.get("discount", 0)),
        )
        item.total = item.calculate_total()
        item.save()


@transaction.atomic
def create_invoice(*, data: dict, items_data: list, user) -> Invoice:
    if not items_data:
        raise ValidationError({"items": ["At least one invoice item is required."]})

    number = generate_invoice_number()
    while Invoice.objects.filter(invoice_number=number).exists():
        number = generate_invoice_number()

    invoice_date = data.get("invoice_date") or timezone.localdate()
    due_date = data.get("due_date")
    if due_date is None:
        due_date = invoice_date + timedelta(days=30)

    invoice = Invoice(
        invoice_number=number,
        customer=data["customer"],
        related_sale=data.get("related_sale"),
        invoice_date=invoice_date,
        due_date=due_date,
        discount=_money(data.get("discount", 0)),
        tax=_money(data.get("tax", 0)),
        paid_amount=_money(data.get("paid_amount", 0)),
        notes=data.get("notes", ""),
        status=InvoiceStatus.DRAFT,
        created_by=user,
    )
    invoice.save()
    _replace_items(invoice, items_data)
    return recalculate_totals(invoice)


@transaction.atomic
def create_invoice_from_sale(*, sale: SalesOrder, user, due_days: int = 30) -> Invoice:
    if sale.status == "cancelled":
        raise ValidationError({"detail": ["Cannot invoice a cancelled sale."]})
    if Invoice.objects.filter(related_sale=sale).exclude(
        status=InvoiceStatus.CANCELLED
    ).exists():
        raise ValidationError({"detail": ["An active invoice already exists for this sale."]})

    items_data = [
        {
            "product": item.product,
            "description": item.product.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "discount": item.discount,
            "tax": item.tax,
        }
        for item in sale.items.select_related("product")
    ]
    return create_invoice(
        data={
            "customer": sale.customer,
            "related_sale": sale,
            "invoice_date": timezone.localdate(),
            "due_date": timezone.localdate() + timedelta(days=due_days),
            "discount": sale.discount,
            "tax": sale.tax,
            "paid_amount": sale.paid_amount,
            "notes": f"Invoice for sale {sale.sale_number}. {sale.notes}".strip(),
        },
        items_data=items_data,
        user=user,
    )


@transaction.atomic
def update_draft_invoice(*, invoice: Invoice, data: dict, items_data: list | None) -> Invoice:
    if invoice.status != InvoiceStatus.DRAFT:
        raise ValidationError({"detail": ["Only draft invoices can be edited."]})

    for field in (
        "customer",
        "invoice_date",
        "due_date",
        "discount",
        "tax",
        "paid_amount",
        "notes",
    ):
        if field in data:
            value = data[field]
            if field in {"discount", "tax", "paid_amount"}:
                value = _money(value)
            setattr(invoice, field, value)
    invoice.save()
    if items_data is not None:
        if not items_data:
            raise ValidationError({"items": ["At least one item is required."]})
        _replace_items(invoice, items_data)
    return recalculate_totals(invoice)


@transaction.atomic
def send_invoice(invoice: Invoice) -> Invoice:
    if invoice.status == InvoiceStatus.CANCELLED:
        raise ValidationError({"detail": ["Cancelled invoices cannot be sent."]})
    if invoice.status == InvoiceStatus.DRAFT:
        invoice.status = InvoiceStatus.SENT
    invoice.sent_at = timezone.now()
    invoice.save(update_fields=["status", "sent_at", "updated_at"])
    return refresh_invoice_status(invoice)


@transaction.atomic
def cancel_invoice(invoice: Invoice) -> Invoice:
    if invoice.status == InvoiceStatus.CANCELLED:
        raise ValidationError({"detail": ["Invoice is already cancelled."]})
    if invoice.paid_amount > 0:
        raise ValidationError(
            {"detail": ["Cannot cancel an invoice that has payments. Reverse payments first."]}
        )
    invoice.status = InvoiceStatus.CANCELLED
    invoice.cancelled_at = timezone.now()
    invoice.save(update_fields=["status", "cancelled_at", "updated_at"])
    return invoice


@transaction.atomic
def apply_amount_to_invoice(*, invoice: Invoice, amount: Decimal) -> Invoice:
    amount = _money(amount)
    if amount <= 0:
        raise ValidationError({"amount": ["Payment amount must be positive."]})
    if invoice.status == InvoiceStatus.CANCELLED:
        raise ValidationError({"detail": ["Cannot pay a cancelled invoice."]})
    if amount > invoice.balance:
        raise ValidationError(
            {
                "amount": [
                    f"Payment exceeds invoice balance of {invoice.balance}."
                ]
            }
        )

    invoice.paid_amount = _money(invoice.paid_amount + amount)
    invoice.balance = _money(invoice.total - invoice.paid_amount)
    invoice.save(update_fields=["paid_amount", "balance", "updated_at"])
    invoice = refresh_invoice_status(invoice)

    if invoice.related_sale_id:
        sale = invoice.related_sale
        sale.paid_amount = _money(sale.paid_amount + amount)
        if sale.paid_amount > sale.grand_total:
            sale.paid_amount = sale.grand_total
        sale.due_amount = _money(sale.grand_total - sale.paid_amount)
        sale.payment_status = derive_payment_status(
            grand_total=sale.grand_total, paid_amount=sale.paid_amount
        )
        sale.save(
            update_fields=["paid_amount", "due_amount", "payment_status", "updated_at"]
        )
    return invoice


def mark_overdue_invoices() -> int:
    today = timezone.localdate()
    qs = Invoice.objects.filter(
        due_date__lt=today,
        balance__gt=0,
        status__in=[
            InvoiceStatus.SENT,
            InvoiceStatus.PARTIALLY_PAID,
            InvoiceStatus.OVERDUE,
        ],
    )
    return qs.update(status=InvoiceStatus.OVERDUE)


def get_customer_invoice_balance(customer) -> Decimal:
    total = (
        Invoice.objects.filter(customer=customer)
        .exclude(status=InvoiceStatus.CANCELLED)
        .aggregate(s=Sum("balance"))
        .get("s")
    )
    return _money(total or 0)


def serialize_invoice_history(customer) -> list:
    qs = (
        Invoice.objects.filter(customer=customer)
        .order_by("-invoice_date", "-id")
        .values(
            "id",
            "invoice_number",
            "invoice_date",
            "due_date",
            "total",
            "paid_amount",
            "balance",
            "status",
        )
    )
    results = []
    for row in qs:
        row["invoice_date"] = row["invoice_date"].isoformat()
        row["due_date"] = row["due_date"].isoformat() if row["due_date"] else None
        row["total"] = str(row["total"])
        row["paid_amount"] = str(row["paid_amount"])
        row["balance"] = str(row["balance"])
        results.append(row)
    return results


def build_print_payload(invoice: Invoice) -> dict:
    invoice = (
        Invoice.objects.select_related("customer", "related_sale", "created_by")
        .prefetch_related("items__product")
        .get(pk=invoice.pk)
    )
    return {
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date.isoformat(),
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "status": invoice.status,
        "customer": {
            "code": invoice.customer.customer_code,
            "name": invoice.customer.name,
            "company_name": invoice.customer.company_name,
            "email": invoice.customer.email,
            "phone": invoice.customer.phone,
            "address": invoice.customer.address,
            "city": invoice.customer.city,
            "state": invoice.customer.state,
            "country": invoice.customer.country,
            "postal_code": invoice.customer.postal_code,
        },
        "related_sale": invoice.related_sale.sale_number if invoice.related_sale else None,
        "totals": {
            "subtotal": str(invoice.subtotal),
            "discount": str(invoice.discount),
            "tax": str(invoice.tax),
            "total": str(invoice.total),
            "paid_amount": str(invoice.paid_amount),
            "balance": str(invoice.balance),
        },
        "notes": invoice.notes,
        "items": [
            {
                "product_code": item.product.product_code if item.product else "",
                "description": item.description or (
                    item.product.name if item.product else ""
                ),
                "quantity": str(item.quantity),
                "unit_price": str(item.unit_price),
                "discount": str(item.discount),
                "tax": str(item.tax),
                "total": str(item.total),
            }
            for item in invoice.items.all()
        ],
        "created_by": getattr(invoice.created_by, "email", None),
    }


def generate_invoice_pdf(invoice: Invoice) -> bytes:
    payload = build_print_payload(invoice)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("INVOICE", styles["Title"]),
        Paragraph(f"<b>{payload['invoice_number']}</b>", styles["Heading2"]),
        Spacer(1, 8),
        Paragraph(
            f"Date: {payload['invoice_date']}<br/>"
            f"Due: {payload['due_date'] or 'N/A'}<br/>"
            f"Status: {payload['status']}",
            styles["Normal"],
        ),
        Spacer(1, 8),
        Paragraph(
            f"<b>Bill To</b><br/>"
            f"{payload['customer']['name']}<br/>"
            f"{payload['customer']['company_name']}<br/>"
            f"{payload['customer']['address']}<br/>"
            f"{payload['customer']['city']}, {payload['customer']['state']} "
            f"{payload['customer']['postal_code']}<br/>"
            f"{payload['customer']['email']} | {payload['customer']['phone']}",
            styles["Normal"],
        ),
        Spacer(1, 12),
    ]
    table_data = [["Code", "Description", "Qty", "Price", "Disc", "Tax", "Total"]]
    for item in payload["items"]:
        table_data.append(
            [
                item["product_code"],
                item["description"][:30],
                item["quantity"],
                item["unit_price"],
                item["discount"],
                item["tax"],
                item["total"],
            ]
        )
    table = Table(table_data, colWidths=[50, 125, 40, 50, 40, 40, 55])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            f"Subtotal: {payload['totals']['subtotal']}<br/>"
            f"Discount: {payload['totals']['discount']}<br/>"
            f"Tax: {payload['totals']['tax']}<br/>"
            f"<b>Total: {payload['totals']['total']}</b><br/>"
            f"Paid: {payload['totals']['paid_amount']}<br/>"
            f"<b>Balance Due: {payload['totals']['balance']}</b>",
            styles["Normal"],
        )
    )
    doc.build(story)
    return buffer.getvalue()


def email_invoice(*, invoice: Invoice, to_email: str | None = None) -> dict:
    email = to_email or invoice.customer.email
    if not email:
        raise ValidationError(
            {"email": ["Customer has no email. Provide to_email."]}
        )
    pdf_bytes = generate_invoice_pdf(invoice)
    message = EmailMessage(
        subject=f"Invoice {invoice.invoice_number}",
        body=(
            f"Dear {invoice.customer.name},\n\n"
            f"Please find attached invoice {invoice.invoice_number}.\n"
            f"Total: {invoice.total}\nBalance due: {invoice.balance}\n"
            f"Due date: {invoice.due_date or 'N/A'}\n\nThank you."
        ),
        to=[email],
    )
    message.attach(f"{invoice.invoice_number}.pdf", pdf_bytes, "application/pdf")
    message.send(fail_silently=False)
    return {"to": email, "invoice_number": invoice.invoice_number}
