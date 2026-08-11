from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel, UserTrackedModel


class CategoryStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class ProductStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class UnitChoices(models.TextChoices):
    PIECE = "pcs", "Piece"
    KG = "kg", "Kilogram"
    GRAM = "g", "Gram"
    LITER = "l", "Liter"
    ML = "ml", "Milliliter"
    BOX = "box", "Box"
    PACK = "pack", "Pack"
    METER = "m", "Meter"
    OTHER = "other", "Other"


def product_image_path(instance, filename):
    return f"products/{instance.product_code or 'new'}/{filename}"


class Category(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=CategoryStatus.choices,
        default=CategoryStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(UserTrackedModel):
    product_code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Internal SKU / product code",
    )
    barcode = models.CharField(max_length=64, blank=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
    )
    unit = models.CharField(
        max_length=16,
        choices=UnitChoices.choices,
        default=UnitChoices.PIECE,
    )
    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text=(
            "Maintained via inventory services. May go negative only when "
            "ALLOW_NEGATIVE_STOCK is enabled."
        ),
    )
    minimum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        validators=[MinValueValidator(Decimal("0.000"))],
    )
    maximum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        validators=[MinValueValidator(Decimal("0.000"))],
    )
    reorder_level = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        validators=[MinValueValidator(Decimal("0.000"))],
    )
    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    product_image = models.ImageField(
        upload_to=product_image_path,
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=16,
        choices=ProductStatus.choices,
        default=ProductStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status", "name"]),
            models.Index(fields=["category", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(purchase_price__gte=0),
                name="product_purchase_price_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(selling_price__gte=0),
                name="product_selling_price_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.product_code} — {self.name}"

    @property
    def is_active(self) -> bool:
        return self.status == ProductStatus.ACTIVE

    @property
    def is_low_stock(self) -> bool:
        threshold = self.reorder_level if self.reorder_level > 0 else self.minimum_stock
        return self.current_stock <= threshold
