from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import UserTrackedModel


class CustomerStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class Customer(UserTrackedModel):
    customer_code = models.CharField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    company_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    tax_number = models.CharField(max_length=64, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default="India")
    postal_code = models.CharField(max_length=20, blank=True)
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    opening_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Positive = customer owes us; negative = we owe customer (advance).",
    )
    status = models.CharField(
        max_length=16,
        choices=CustomerStatus.choices,
        default=CustomerStatus.ACTIVE,
        db_index=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status", "name"]),
            models.Index(fields=["city", "state"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(credit_limit__gte=0),
                name="customer_credit_limit_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.customer_code} — {self.name}"

    @property
    def is_active(self) -> bool:
        return self.status == CustomerStatus.ACTIVE
