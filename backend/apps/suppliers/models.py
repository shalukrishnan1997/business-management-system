from decimal import Decimal

from django.db import models

from apps.common.models import UserTrackedModel


class SupplierStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class Supplier(UserTrackedModel):
    supplier_code = models.CharField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    company_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    tax_number = models.CharField(max_length=64, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default="India")
    opening_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Positive = we owe supplier (payable); negative = supplier advance.",
    )
    status = models.CharField(
        max_length=16,
        choices=SupplierStatus.choices,
        default=SupplierStatus.ACTIVE,
        db_index=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status", "name"]),
            models.Index(fields=["city", "country"]),
        ]

    def __str__(self):
        return f"{self.supplier_code} — {self.name}"

    @property
    def is_active(self) -> bool:
        return self.status == SupplierStatus.ACTIVE
