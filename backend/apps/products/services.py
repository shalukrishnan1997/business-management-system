"""
Product/category services.

Opening stock is applied via inventory ledger (Phase 9+).
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Max, Q

from .models import Category, CategoryStatus, Product, ProductStatus


def generate_product_code() -> str:
    latest = (
        Product.objects.filter(product_code__startswith="PRD-")
        .aggregate(Max("product_code"))
        .get("product_code__max")
    )
    if not latest:
        next_num = 1
    else:
        try:
            next_num = int(str(latest).split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            next_num = Product.objects.count() + 1
    return f"PRD-{next_num:04d}"


@transaction.atomic
def create_product(*, data: dict, user, opening_stock: Decimal | None = None) -> Product:
    payload = dict(data)
    raw_code = (payload.pop("product_code", None) or "").strip()
    if raw_code:
        code = raw_code.upper()
    else:
        code = generate_product_code()
        while Product.objects.filter(product_code=code).exists():
            try:
                n = int(code.split("-", 1)[1]) + 1
            except (IndexError, ValueError):
                n = Product.objects.count() + 1
            code = f"PRD-{n:04d}"

    payload.pop("current_stock", None)

    if opening_stock is not None and Decimal(str(opening_stock)) < 0:
        raise ValueError("Opening stock cannot be negative.")

    product = Product(
        product_code=code,
        created_by=user,
        current_stock=Decimal("0.000"),
        **payload,
    )
    product.save()

    if opening_stock is not None and Decimal(str(opening_stock)) > 0:
        from apps.inventory.services import record_opening_stock

        record_opening_stock(
            product=product, quantity=opening_stock, user=user
        )
        product.refresh_from_db()

    return product


def deactivate_product(product: Product) -> Product:
    product.status = ProductStatus.INACTIVE
    product.save(update_fields=["status", "updated_at"])
    return product


def activate_product(product: Product) -> Product:
    product.status = ProductStatus.ACTIVE
    product.save(update_fields=["status", "updated_at"])
    return product


def deactivate_category(category: Category) -> Category:
    category.status = CategoryStatus.INACTIVE
    category.save(update_fields=["status", "updated_at"])
    return category


def activate_category(category: Category) -> Category:
    category.status = CategoryStatus.ACTIVE
    category.save(update_fields=["status", "updated_at"])
    return category


def update_product_prices(
    product: Product,
    *,
    purchase_price: Decimal | None = None,
    selling_price: Decimal | None = None,
    tax_percentage: Decimal | None = None,
) -> Product:
    fields = ["updated_at"]
    if purchase_price is not None:
        product.purchase_price = purchase_price
        fields.append("purchase_price")
    if selling_price is not None:
        product.selling_price = selling_price
        fields.append("selling_price")
    if tax_percentage is not None:
        product.tax_percentage = tax_percentage
        fields.append("tax_percentage")
    product.save(update_fields=fields)
    return product


def low_stock_queryset():
    return Product.objects.filter(status=ProductStatus.ACTIVE).filter(
        Q(reorder_level__gt=0, current_stock__lte=F("reorder_level"))
        | Q(reorder_level=0, current_stock__lte=F("minimum_stock"))
    )


def lookup_product(*, sku: str | None = None, barcode: str | None = None) -> Product | None:
    qs = Product.objects.select_related("category", "supplier")
    if sku:
        return qs.filter(product_code__iexact=sku.strip()).first()
    if barcode:
        return qs.filter(barcode__iexact=barcode.strip()).first()
    return None


def get_inventory_history(product: Product) -> list:
    from apps.inventory.serializers import StockTransactionSerializer
    from apps.inventory.services import get_product_stock_history

    qs = get_product_stock_history(product)
    return StockTransactionSerializer(qs, many=True).data
