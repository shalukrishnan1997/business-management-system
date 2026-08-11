"""
Quotation workflow: draft → sent → accepted/rejected/expired → convert to sale.
"""
from decimal import Decimal
from io import BytesIO

from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework.exceptions import ValidationError

from apps.products.models import Product
from apps.sales.services import create_sale

from .models import Quotation, QuotationItem, QuotationStatus


def generate_quotation_number() -> str:
    latest = (
        Quotation.objects.filter(quotation_number__startswith="QTN-")
        .aggregate(Max("quotation_number"))
        .get("quotation_number__max")
    )
    if not latest:
        next_num = 1
    else:
        try:
            next_num = int(str(latest).split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            next_num = Quotation.objects.count() + 1
    return f"QTN-{next_num:04d}"


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _qty(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"))


def recalculate_totals(quotation: Quotation) -> Quotation:
    items = list(quotation.items.all())
    subtotal = sum((i.quantity * i.unit_price for i in items), Decimal("0.00"))
    for item in items:
        item.total = item.calculate_total()
        item.save(update_fields=["total"])
    quotation.subtotal = _money(subtotal)
    lines_net = sum((i.total for i in items), Decimal("0.00"))
    quotation.grand_total = _money(lines_net - quotation.discount + quotation.tax)
    quotation.save(update_fields=["subtotal", "grand_total", "updated_at"])
    return quotation


def _replace_items(quotation: Quotation, items_data: list) -> None:
    quotation.items.all().delete()
    for row in items_data:
        product = row["product"]
        if isinstance(product, int):
            product = Product.objects.get(pk=product)
        item = QuotationItem(
            quotation=quotation,
            product=product,
            quantity=_qty(row["quantity"]),
            unit_price=_money(row["unit_price"]),
            tax=_money(row.get("tax", 0)),
            discount=_money(row.get("discount", 0)),
        )
        item.total = item.calculate_total()
        item.save()


def maybe_mark_expired(quotation: Quotation) -> Quotation:
    if (
        quotation.status in {QuotationStatus.DRAFT, QuotationStatus.SENT}
        and quotation.is_past_valid_until
    ):
        quotation.status = QuotationStatus.EXPIRED
        quotation.save(update_fields=["status", "updated_at"])
    return quotation


@transaction.atomic
def create_quotation(*, data: dict, items_data: list, user) -> Quotation:
    if not items_data:
        raise ValidationError({"items": ["At least one quotation item is required."]})

    number = data.get("quotation_number") or generate_quotation_number()
    while Quotation.objects.filter(quotation_number=number).exists():
        number = generate_quotation_number()

    quotation = Quotation(
        quotation_number=number,
        customer=data["customer"],
        quotation_date=data.get("quotation_date") or timezone.localdate(),
        valid_until=data.get("valid_until"),
        discount=_money(data.get("discount", 0)),
        tax=_money(data.get("tax", 0)),
        notes=data.get("notes", ""),
        status=QuotationStatus.DRAFT,
        created_by=user,
    )
    quotation.save()
    _replace_items(quotation, items_data)
    return recalculate_totals(quotation)


@transaction.atomic
def update_draft_quotation(
    *, quotation: Quotation, data: dict, items_data: list | None
) -> Quotation:
    quotation = maybe_mark_expired(quotation)
    if quotation.status != QuotationStatus.DRAFT:
        raise ValidationError({"detail": ["Only draft quotations can be edited."]})

    for field in (
        "customer",
        "quotation_date",
        "valid_until",
        "discount",
        "tax",
        "notes",
    ):
        if field in data:
            value = data[field]
            if field in {"discount", "tax"}:
                value = _money(value)
            setattr(quotation, field, value)
    quotation.save()
    if items_data is not None:
        if not items_data:
            raise ValidationError({"items": ["At least one item is required."]})
        _replace_items(quotation, items_data)
    return recalculate_totals(quotation)


@transaction.atomic
def send_quotation(quotation: Quotation) -> Quotation:
    quotation = maybe_mark_expired(quotation)
    if quotation.status == QuotationStatus.EXPIRED:
        raise ValidationError({"detail": ["Cannot send an expired quotation."]})
    if quotation.status not in {QuotationStatus.DRAFT, QuotationStatus.SENT}:
        raise ValidationError({"detail": ["Only draft quotations can be sent."]})
    if not quotation.items.exists():
        raise ValidationError({"items": ["Add items before sending."]})
    quotation.status = QuotationStatus.SENT
    quotation.sent_at = timezone.now()
    quotation.save(update_fields=["status", "sent_at", "updated_at"])
    return quotation


@transaction.atomic
def accept_quotation(quotation: Quotation) -> Quotation:
    quotation = maybe_mark_expired(quotation)
    if quotation.status == QuotationStatus.EXPIRED:
        raise ValidationError({"detail": ["Cannot accept an expired quotation."]})
    if quotation.status != QuotationStatus.SENT:
        raise ValidationError({"detail": ["Only sent quotations can be accepted."]})
    quotation.status = QuotationStatus.ACCEPTED
    quotation.accepted_at = timezone.now()
    quotation.save(update_fields=["status", "accepted_at", "updated_at"])
    return quotation


@transaction.atomic
def reject_quotation(quotation: Quotation) -> Quotation:
    quotation = maybe_mark_expired(quotation)
    if quotation.status != QuotationStatus.SENT:
        raise ValidationError({"detail": ["Only sent quotations can be rejected."]})
    quotation.status = QuotationStatus.REJECTED
    quotation.rejected_at = timezone.now()
    quotation.save(update_fields=["status", "rejected_at", "updated_at"])
    return quotation


@transaction.atomic
def convert_quotation_to_sale(*, quotation: Quotation, user):
    quotation = maybe_mark_expired(quotation)
    if quotation.converted_sale_id:
        raise ValidationError({"detail": ["Quotation already converted to a sale."]})
    if quotation.status != QuotationStatus.ACCEPTED:
        raise ValidationError(
            {"detail": ["Only accepted quotations can be converted to a sale."]}
        )
    if quotation.is_past_valid_until:
        quotation.status = QuotationStatus.EXPIRED
        quotation.save(update_fields=["status", "updated_at"])
        raise ValidationError({"detail": ["Quotation has expired."]})

    items_data = [
        {
            "product": item.product,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "discount": item.discount,
            "tax": item.tax,
        }
        for item in quotation.items.select_related("product")
    ]
    sale = create_sale(
        data={
            "customer": quotation.customer,
            "sale_date": timezone.localdate(),
            "discount": quotation.discount,
            "tax": quotation.tax,
            "shipping": Decimal("0.00"),
            "paid_amount": Decimal("0.00"),
            "notes": f"Converted from {quotation.quotation_number}. {quotation.notes}".strip(),
        },
        items_data=items_data,
        user=user,
    )
    quotation.converted_sale = sale
    quotation.save(update_fields=["converted_sale", "updated_at"])
    return sale


def build_print_payload(quotation: Quotation) -> dict:
    quotation = (
        Quotation.objects.select_related("customer", "created_by", "converted_sale")
        .prefetch_related("items__product")
        .get(pk=quotation.pk)
    )
    return {
        "quotation_number": quotation.quotation_number,
        "quotation_date": quotation.quotation_date.isoformat(),
        "valid_until": quotation.valid_until.isoformat()
        if quotation.valid_until
        else None,
        "status": quotation.status,
        "customer": {
            "code": quotation.customer.customer_code,
            "name": quotation.customer.name,
            "company_name": quotation.customer.company_name,
            "email": quotation.customer.email,
            "phone": quotation.customer.phone,
            "address": quotation.customer.address,
            "city": quotation.customer.city,
            "country": quotation.customer.country,
        },
        "totals": {
            "subtotal": str(quotation.subtotal),
            "discount": str(quotation.discount),
            "tax": str(quotation.tax),
            "grand_total": str(quotation.grand_total),
        },
        "notes": quotation.notes,
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
            for item in quotation.items.all()
        ],
        "converted_sale_id": quotation.converted_sale_id,
        "created_by": getattr(quotation.created_by, "email", None),
    }


def generate_quotation_pdf(quotation: Quotation) -> bytes:
    """Generate a simple professional PDF using ReportLab."""
    payload = build_print_payload(quotation)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("QUOTATION", styles["Title"]),
        Paragraph(f"<b>{payload['quotation_number']}</b>", styles["Heading2"]),
        Spacer(1, 8),
        Paragraph(
            f"Date: {payload['quotation_date']}<br/>"
            f"Valid until: {payload['valid_until'] or 'N/A'}<br/>"
            f"Status: {payload['status']}",
            styles["Normal"],
        ),
        Spacer(1, 8),
        Paragraph(
            f"<b>Customer</b><br/>"
            f"{payload['customer']['name']}<br/>"
            f"{payload['customer']['company_name']}<br/>"
            f"{payload['customer']['email']} | {payload['customer']['phone']}",
            styles["Normal"],
        ),
        Spacer(1, 12),
    ]

    table_data = [["Code", "Product", "Qty", "Price", "Disc", "Tax", "Total"]]
    for item in payload["items"]:
        table_data.append(
            [
                item["product_code"],
                item["product_name"][:28],
                item["quantity"],
                item["unit_price"],
                item["discount"],
                item["tax"],
                item["total"],
            ]
        )
    table = Table(table_data, colWidths=[55, 120, 45, 50, 45, 45, 55])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
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
            f"<b>Grand Total: {payload['totals']['grand_total']}</b>",
            styles["Normal"],
        )
    )
    if payload["notes"]:
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"Notes: {payload['notes']}", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()


def email_quotation(*, quotation: Quotation, to_email: str | None = None) -> dict:
    customer_email = to_email or quotation.customer.email
    if not customer_email:
        raise ValidationError(
            {"email": ["Customer has no email. Provide to_email in the request."]}
        )

    pdf_bytes = generate_quotation_pdf(quotation)
    subject = f"Quotation {quotation.quotation_number}"
    body = (
        f"Dear {quotation.customer.name},\n\n"
        f"Please find attached quotation {quotation.quotation_number}.\n"
        f"Grand total: {quotation.grand_total}\n"
        f"Valid until: {quotation.valid_until or 'N/A'}\n\n"
        f"Thank you."
    )
    message = EmailMessage(
        subject=subject,
        body=body,
        to=[customer_email],
    )
    message.attach(
        f"{quotation.quotation_number}.pdf",
        pdf_bytes,
        "application/pdf",
    )
    message.send(fail_silently=False)
    return {"to": customer_email, "quotation_number": quotation.quotation_number}
