"""
Employee services — codes, activate/deactivate, org validation.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (
    Department,
    Designation,
    Employee,
    EmployeeStatus,
    EmploymentType,
    OrgUnitStatus,
)


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def generate_employee_code() -> str:
    latest = (
        Employee.objects.filter(employee_code__startswith="EMP-")
        .aggregate(Max("employee_code"))
        .get("employee_code__max")
    )
    if not latest:
        next_num = 1
    else:
        try:
            next_num = int(str(latest).split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            next_num = Employee.objects.count() + 1
    return f"EMP-{next_num:04d}"


def activate_department(department: Department) -> Department:
    department.status = OrgUnitStatus.ACTIVE
    department.save(update_fields=["status", "updated_at"])
    return department


def deactivate_department(department: Department) -> Department:
    department.status = OrgUnitStatus.INACTIVE
    department.save(update_fields=["status", "updated_at"])
    return department


def activate_designation(designation: Designation) -> Designation:
    designation.status = OrgUnitStatus.ACTIVE
    designation.save(update_fields=["status", "updated_at"])
    return designation


def deactivate_designation(designation: Designation) -> Designation:
    designation.status = OrgUnitStatus.INACTIVE
    designation.save(update_fields=["status", "updated_at"])
    return designation


def activate_employee(employee: Employee) -> Employee:
    employee.status = EmployeeStatus.ACTIVE
    employee.save(update_fields=["status", "updated_at"])
    return employee


def deactivate_employee(employee: Employee) -> Employee:
    employee.status = EmployeeStatus.INACTIVE
    employee.save(update_fields=["status", "updated_at"])
    return employee


def _validate_org(*, department: Department, designation: Designation) -> None:
    if designation.department_id != department.id:
        raise ValidationError(
            {"designation": ["Designation does not belong to the selected department."]}
        )
    if department.status != OrgUnitStatus.ACTIVE:
        raise ValidationError({"department": ["Department is inactive."]})
    if designation.status != OrgUnitStatus.ACTIVE:
        raise ValidationError({"designation": ["Designation is inactive."]})


@transaction.atomic
def create_employee(*, data: dict, user) -> Employee:
    department = data["department"]
    designation = data["designation"]
    _validate_org(department=department, designation=designation)

    raw_code = (data.get("employee_code") or "").strip()
    if raw_code:
        code = raw_code.upper()
        if Employee.objects.filter(employee_code=code).exists():
            raise ValidationError(
                {"employee_code": ["This employee code already exists."]}
            )
    else:
        code = generate_employee_code()
        while Employee.objects.filter(employee_code=code).exists():
            try:
                n = int(code.split("-", 1)[1]) + 1
            except (IndexError, ValueError):
                n = Employee.objects.count() + 1
            code = f"EMP-{n:04d}"

    linked_user = data.get("user")
    if linked_user and Employee.objects.filter(user=linked_user).exists():
        raise ValidationError({"user": ["This user is already linked to an employee."]})

    employee = Employee(
        employee_code=code,
        first_name=data["first_name"].strip(),
        last_name=(data.get("last_name") or "").strip(),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        department=department,
        designation=designation,
        user=linked_user,
        employment_type=data.get("employment_type") or EmploymentType.FULL_TIME,
        join_date=data.get("join_date") or timezone.localdate(),
        end_date=data.get("end_date"),
        basic_salary=_money(data.get("basic_salary", 0)),
        address=data.get("address", ""),
        city=data.get("city", ""),
        state=data.get("state", ""),
        country=data.get("country", "India"),
        notes=data.get("notes", ""),
        status=data.get("status") or EmployeeStatus.ACTIVE,
        created_by=user,
    )
    employee.save()
    return employee


@transaction.atomic
def update_employee(*, employee: Employee, data: dict) -> Employee:
    department = data.get("department", employee.department)
    designation = data.get("designation", employee.designation)
    _validate_org(department=department, designation=designation)

    if "user" in data:
        linked_user = data["user"]
        if (
            linked_user
            and Employee.objects.filter(user=linked_user)
            .exclude(pk=employee.pk)
            .exists()
        ):
            raise ValidationError(
                {"user": ["This user is already linked to an employee."]}
            )
        employee.user = linked_user

    for field in (
        "first_name",
        "last_name",
        "email",
        "phone",
        "employment_type",
        "join_date",
        "end_date",
        "address",
        "city",
        "state",
        "country",
        "notes",
        "status",
    ):
        if field in data:
            value = data[field]
            if field in {"first_name", "last_name"} and isinstance(value, str):
                value = value.strip()
            setattr(employee, field, value)

    if "basic_salary" in data:
        employee.basic_salary = _money(data["basic_salary"])

    employee.department = department
    employee.designation = designation
    employee.save()
    return employee
