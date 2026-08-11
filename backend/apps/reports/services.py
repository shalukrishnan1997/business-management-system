"""
Dashboard KPIs, chart series, recent activity, and filtered report builders.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from apps.customers.models import Customer, CustomerStatus
from apps.employees.models import Employee, EmployeeStatus
from apps.expenses.models import Expense, ExpenseStatus
from apps.invoices.models import Invoice, InvoiceStatus
from apps.payments.models import Payment, PaymentType
from apps.products.models import Product, ProductStatus
from apps.products.services import low_stock_queryset
from apps.purchases.models import Purchase, PurchaseStatus
from apps.sales.models import SaleStatus, SalesOrder
from apps.suppliers.models import Supplier, SupplierStatus


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _str_money(value) -> str:
    return str(_money(value))


def _parse_period(date_from=None, date_to=None):
    today = timezone.localdate()
    if date_to is None:
        date_to = today
    if date_from is None:
        date_from = date_to - timedelta(days=29)
    return date_from, date_to


def get_dashboard_kpis() -> dict:
    today = timezone.localdate()
    month_start = today.replace(day=1)

    sales_qs = SalesOrder.objects.exclude(status=SaleStatus.CANCELLED)
    purchases_qs = Purchase.objects.exclude(purchase_status=PurchaseStatus.CANCELLED)
    invoices_open = Invoice.objects.exclude(status=InvoiceStatus.CANCELLED).filter(
        balance__gt=0
    )
    expenses_month = Expense.objects.filter(
        status=ExpenseStatus.RECORDED, expense_date__gte=month_start
    )

    sales_today = sales_qs.filter(sale_date=today).aggregate(s=Sum("grand_total"))["s"]
    sales_month = sales_qs.filter(sale_date__gte=month_start).aggregate(
        s=Sum("grand_total")
    )["s"]
    purchases_month = purchases_qs.filter(purchase_date__gte=month_start).aggregate(
        s=Sum("grand_total")
    )["s"]
    receivables = invoices_open.aggregate(s=Sum("balance"))["s"]
    expenses_total = expenses_month.aggregate(s=Sum("amount"))["s"]

    return {
        "as_of": today.isoformat(),
        "counts": {
            "customers": Customer.objects.filter(status=CustomerStatus.ACTIVE).count(),
            "suppliers": Supplier.objects.filter(status=SupplierStatus.ACTIVE).count(),
            "products": Product.objects.filter(status=ProductStatus.ACTIVE).count(),
            "low_stock": low_stock_queryset().count(),
            "employees": Employee.objects.filter(status=EmployeeStatus.ACTIVE).count(),
            "overdue_invoices": Invoice.objects.filter(
                status=InvoiceStatus.OVERDUE
            ).count(),
        },
        "money": {
            "sales_today": _str_money(sales_today),
            "sales_month": _str_money(sales_month),
            "purchases_month": _str_money(purchases_month),
            "receivables": _str_money(receivables),
            "expenses_month": _str_money(expenses_total),
        },
    }


def get_dashboard_charts(*, days: int = 30) -> dict:
    days = max(1, min(int(days or 30), 365))
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)

    # Group by DateField directly (TruncDate breaks on SQLite DateFields).
    sales_rows = (
        SalesOrder.objects.exclude(status=SaleStatus.CANCELLED)
        .filter(sale_date__gte=start, sale_date__lte=today)
        .values("sale_date")
        .annotate(total=Sum("grand_total"), count=Count("id"))
        .order_by("sale_date")
    )
    purchase_rows = (
        Purchase.objects.exclude(purchase_status=PurchaseStatus.CANCELLED)
        .filter(purchase_date__gte=start, purchase_date__lte=today)
        .values("purchase_date")
        .annotate(total=Sum("grand_total"), count=Count("id"))
        .order_by("purchase_date")
    )
    expense_by_cat = (
        Expense.objects.filter(
            status=ExpenseStatus.RECORDED,
            expense_date__gte=start,
            expense_date__lte=today,
        )
        .values("category__name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )
    invoice_status = (
        Invoice.objects.exclude(status=InvoiceStatus.CANCELLED)
        .values("status")
        .annotate(count=Count("id"), total=Sum("total"), balance=Sum("balance"))
        .order_by("status")
    )

    sales_map = {r["sale_date"]: r for r in sales_rows}
    purchase_map = {r["purchase_date"]: r for r in purchase_rows}
    series = []
    cursor = start
    while cursor <= today:
        s = sales_map.get(cursor)
        p = purchase_map.get(cursor)
        series.append(
            {
                "date": cursor.isoformat(),
                "sales": _str_money(s["total"] if s else 0),
                "purchases": _str_money(p["total"] if p else 0),
                "sales_count": s["count"] if s else 0,
                "purchases_count": p["count"] if p else 0,
            }
        )
        cursor += timedelta(days=1)

    return {
        "period": {"from": start.isoformat(), "to": today.isoformat(), "days": days},
        "sales_vs_purchases": series,
        "expenses_by_category": [
            {
                "category": row["category__name"] or "Uncategorized",
                "total": _str_money(row["total"]),
                "count": row["count"],
            }
            for row in expense_by_cat
        ],
        "invoices_by_status": [
            {
                "status": row["status"],
                "count": row["count"],
                "total": _str_money(row["total"]),
                "balance": _str_money(row["balance"]),
            }
            for row in invoice_status
        ],
    }


def get_recent_activity(*, limit: int = 15) -> dict:
    limit = max(1, min(int(limit or 15), 50))
    items = []

    for sale in (
        SalesOrder.objects.select_related("customer")
        .order_by("-created_at")[:limit]
    ):
        items.append(
            {
                "type": "sale",
                "reference": sale.sale_number,
                "title": f"Sale to {sale.customer.name}",
                "amount": _str_money(sale.grand_total),
                "status": sale.status,
                "at": sale.created_at.isoformat(),
            }
        )
    for purchase in (
        Purchase.objects.select_related("supplier")
        .order_by("-created_at")[:limit]
    ):
        items.append(
            {
                "type": "purchase",
                "reference": purchase.purchase_number,
                "title": f"Purchase from {purchase.supplier.name}",
                "amount": _str_money(purchase.grand_total),
                "status": purchase.purchase_status,
                "at": purchase.created_at.isoformat(),
            }
        )
    for invoice in (
        Invoice.objects.select_related("customer")
        .order_by("-created_at")[:limit]
    ):
        items.append(
            {
                "type": "invoice",
                "reference": invoice.invoice_number,
                "title": f"Invoice for {invoice.customer.name}",
                "amount": _str_money(invoice.total),
                "status": invoice.status,
                "at": invoice.created_at.isoformat(),
            }
        )
    for payment in Payment.objects.order_by("-created_at")[:limit]:
        party = (
            payment.customer.name
            if payment.customer_id
            else (payment.supplier.name if payment.supplier_id else "—")
        )
        items.append(
            {
                "type": "payment",
                "reference": payment.payment_number,
                "title": f"{payment.payment_type} — {party}",
                "amount": _str_money(payment.amount),
                "status": payment.payment_method,
                "at": payment.created_at.isoformat(),
            }
        )
    for expense in (
        Expense.objects.select_related("category")
        .order_by("-created_at")[:limit]
    ):
        items.append(
            {
                "type": "expense",
                "reference": expense.expense_number,
                "title": expense.title,
                "amount": _str_money(expense.amount),
                "status": expense.status,
                "at": expense.created_at.isoformat(),
            }
        )

    items.sort(key=lambda x: x["at"], reverse=True)
    return {"results": items[:limit]}


def report_sales(*, date_from=None, date_to=None) -> dict:
    date_from, date_to = _parse_period(date_from, date_to)
    qs = (
        SalesOrder.objects.select_related("customer")
        .exclude(status=SaleStatus.CANCELLED)
        .filter(sale_date__gte=date_from, sale_date__lte=date_to)
        .order_by("-sale_date", "-id")
    )
    rows = [
        {
            "id": s.id,
            "sale_number": s.sale_number,
            "sale_date": s.sale_date.isoformat(),
            "customer": s.customer.name,
            "customer_code": s.customer.customer_code,
            "grand_total": _str_money(s.grand_total),
            "paid_amount": _str_money(s.paid_amount),
            "due_amount": _str_money(s.due_amount),
            "payment_status": s.payment_status,
            "status": s.status,
        }
        for s in qs
    ]
    agg = qs.aggregate(
        total=Sum("grand_total"),
        paid=Sum("paid_amount"),
        due=Sum("due_amount"),
        count=Count("id"),
    )
    return {
        "report": "sales",
        "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
        "summary": {
            "count": agg["count"] or 0,
            "grand_total": _str_money(agg["total"]),
            "paid_amount": _str_money(agg["paid"]),
            "due_amount": _str_money(agg["due"]),
        },
        "rows": rows,
        "columns": [
            "sale_number",
            "sale_date",
            "customer",
            "grand_total",
            "paid_amount",
            "due_amount",
            "payment_status",
            "status",
        ],
    }


def report_purchases(*, date_from=None, date_to=None) -> dict:
    date_from, date_to = _parse_period(date_from, date_to)
    qs = (
        Purchase.objects.select_related("supplier")
        .exclude(purchase_status=PurchaseStatus.CANCELLED)
        .filter(purchase_date__gte=date_from, purchase_date__lte=date_to)
        .order_by("-purchase_date", "-id")
    )
    rows = [
        {
            "id": p.id,
            "purchase_number": p.purchase_number,
            "purchase_date": p.purchase_date.isoformat(),
            "supplier": p.supplier.name,
            "supplier_code": p.supplier.supplier_code,
            "grand_total": _str_money(p.grand_total),
            "paid_amount": _str_money(p.paid_amount),
            "due_amount": _str_money(p.due_amount),
            "payment_status": p.payment_status,
            "purchase_status": p.purchase_status,
        }
        for p in qs
    ]
    agg = qs.aggregate(
        total=Sum("grand_total"),
        paid=Sum("paid_amount"),
        due=Sum("due_amount"),
        count=Count("id"),
    )
    return {
        "report": "purchases",
        "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
        "summary": {
            "count": agg["count"] or 0,
            "grand_total": _str_money(agg["total"]),
            "paid_amount": _str_money(agg["paid"]),
            "due_amount": _str_money(agg["due"]),
        },
        "rows": rows,
        "columns": [
            "purchase_number",
            "purchase_date",
            "supplier",
            "grand_total",
            "paid_amount",
            "due_amount",
            "payment_status",
            "purchase_status",
        ],
    }


def report_invoices(*, date_from=None, date_to=None) -> dict:
    date_from, date_to = _parse_period(date_from, date_to)
    qs = (
        Invoice.objects.select_related("customer")
        .exclude(status=InvoiceStatus.CANCELLED)
        .filter(invoice_date__gte=date_from, invoice_date__lte=date_to)
        .order_by("-invoice_date", "-id")
    )
    rows = [
        {
            "id": i.id,
            "invoice_number": i.invoice_number,
            "invoice_date": i.invoice_date.isoformat(),
            "due_date": i.due_date.isoformat() if i.due_date else None,
            "customer": i.customer.name,
            "total": _str_money(i.total),
            "paid_amount": _str_money(i.paid_amount),
            "balance": _str_money(i.balance),
            "status": i.status,
        }
        for i in qs
    ]
    agg = qs.aggregate(
        total=Sum("total"),
        paid=Sum("paid_amount"),
        balance=Sum("balance"),
        count=Count("id"),
    )
    return {
        "report": "invoices",
        "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
        "summary": {
            "count": agg["count"] or 0,
            "total": _str_money(agg["total"]),
            "paid_amount": _str_money(agg["paid"]),
            "balance": _str_money(agg["balance"]),
        },
        "rows": rows,
        "columns": [
            "invoice_number",
            "invoice_date",
            "due_date",
            "customer",
            "total",
            "paid_amount",
            "balance",
            "status",
        ],
    }


def report_payments(*, date_from=None, date_to=None) -> dict:
    date_from, date_to = _parse_period(date_from, date_to)
    qs = (
        Payment.objects.select_related("customer", "supplier")
        .filter(payment_date__gte=date_from, payment_date__lte=date_to)
        .order_by("-payment_date", "-id")
    )
    rows = [
        {
            "id": p.id,
            "payment_number": p.payment_number,
            "payment_date": p.payment_date.isoformat(),
            "payment_type": p.payment_type,
            "party": (
                p.customer.name
                if p.customer_id
                else (p.supplier.name if p.supplier_id else "")
            ),
            "amount": _str_money(p.amount),
            "payment_method": p.payment_method,
            "reference_type": p.reference_type,
            "reference_id": p.reference_id,
        }
        for p in qs
    ]
    receipts = qs.filter(payment_type=PaymentType.CUSTOMER_RECEIPT).aggregate(
        s=Sum("amount")
    )["s"]
    supplier_payments = qs.filter(payment_type=PaymentType.SUPPLIER_PAYMENT).aggregate(
        s=Sum("amount")
    )["s"]
    return {
        "report": "payments",
        "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
        "summary": {
            "count": qs.count(),
            "receipts": _str_money(receipts),
            "supplier_payments": _str_money(supplier_payments),
        },
        "rows": rows,
        "columns": [
            "payment_number",
            "payment_date",
            "payment_type",
            "party",
            "amount",
            "payment_method",
            "reference_type",
            "reference_id",
        ],
    }


def report_expenses(*, date_from=None, date_to=None) -> dict:
    date_from, date_to = _parse_period(date_from, date_to)
    qs = (
        Expense.objects.select_related("category")
        .filter(
            status=ExpenseStatus.RECORDED,
            expense_date__gte=date_from,
            expense_date__lte=date_to,
        )
        .order_by("-expense_date", "-id")
    )
    rows = [
        {
            "id": e.id,
            "expense_number": e.expense_number,
            "expense_date": e.expense_date.isoformat(),
            "category": e.category.name,
            "title": e.title,
            "vendor_name": e.vendor_name,
            "amount": _str_money(e.amount),
            "payment_method": e.payment_method,
        }
        for e in qs
    ]
    agg = qs.aggregate(total=Sum("amount"), count=Count("id"))
    return {
        "report": "expenses",
        "period": {"from": date_from.isoformat(), "to": date_to.isoformat()},
        "summary": {
            "count": agg["count"] or 0,
            "total_amount": _str_money(agg["total"]),
        },
        "rows": rows,
        "columns": [
            "expense_number",
            "expense_date",
            "category",
            "title",
            "vendor_name",
            "amount",
            "payment_method",
        ],
    }


def report_inventory() -> dict:
    qs = Product.objects.select_related("category").filter(status=ProductStatus.ACTIVE)
    low_ids = set(low_stock_queryset().values_list("id", flat=True))
    rows = [
        {
            "id": p.id,
            "product_code": p.product_code,
            "name": p.name,
            "category": p.category.name if p.category_id else "",
            "current_stock": str(p.current_stock),
            "minimum_stock": str(p.minimum_stock),
            "reorder_level": str(p.reorder_level),
            "is_low_stock": p.id in low_ids,
            "selling_price": _str_money(p.selling_price),
        }
        for p in qs.order_by("name")
    ]
    return {
        "report": "inventory",
        "period": {"from": None, "to": None},
        "summary": {
            "count": len(rows),
            "low_stock_count": len(low_ids),
        },
        "rows": rows,
        "columns": [
            "product_code",
            "name",
            "category",
            "current_stock",
            "minimum_stock",
            "reorder_level",
            "is_low_stock",
            "selling_price",
        ],
    }


REPORT_BUILDERS = {
    "sales": report_sales,
    "purchases": report_purchases,
    "invoices": report_invoices,
    "payments": report_payments,
    "expenses": report_expenses,
    "inventory": lambda **kwargs: report_inventory(),
}
