from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel, UserTrackedModel


class OrgUnitStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class EmployeeStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class EmploymentType(models.TextChoices):
    FULL_TIME = "full_time", "Full Time"
    PART_TIME = "part_time", "Part Time"
    CONTRACT = "contract", "Contract"
    INTERN = "intern", "Intern"


class Department(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=OrgUnitStatus.choices,
        default=OrgUnitStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Designation(TimeStampedModel):
    name = models.CharField(max_length=120, db_index=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="designations",
    )
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=OrgUnitStatus.choices,
        default=OrgUnitStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"],
                name="unique_designation_per_department",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.department.name})"


class Employee(UserTrackedModel):
    employee_code = models.CharField(max_length=32, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="employees",
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.PROTECT,
        related_name="employees",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile",
        help_text="Optional login account linked to this employee.",
    )
    employment_type = models.CharField(
        max_length=16,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    join_date = models.DateField(default=timezone.localdate, db_index=True)
    end_date = models.DateField(null=True, blank=True)
    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Light payroll field for MVP; not a full payroll engine.",
    )
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default="India")
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=EmployeeStatus.choices,
        default=EmployeeStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["first_name", "last_name"]
        indexes = [
            models.Index(fields=["status", "department"]),
            models.Index(fields=["join_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(basic_salary__gte=0),
                name="employee_basic_salary_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.employee_code} — {self.full_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_active(self) -> bool:
        return self.status == EmployeeStatus.ACTIVE
