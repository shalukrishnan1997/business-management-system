from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Department,
    Designation,
    Employee,
    EmployeeStatus,
    EmploymentType,
)

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    designations_count = serializers.IntegerField(read_only=True, required=False)
    employees_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Department
        fields = (
            "id",
            "name",
            "description",
            "status",
            "designations_count",
            "employees_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "designations_count",
            "employees_count",
            "created_at",
            "updated_at",
        )


class DesignationSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    employees_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Designation
        fields = (
            "id",
            "name",
            "department",
            "department_name",
            "description",
            "status",
            "employees_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "department_name",
            "employees_count",
            "created_at",
            "updated_at",
        )


class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    designation_name = serializers.CharField(source="designation.name", read_only=True)
    full_name = serializers.CharField(read_only=True)
    user_email = serializers.EmailField(
        source="user.email", read_only=True, default=None
    )
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )

    class Meta:
        model = Employee
        fields = (
            "id",
            "employee_code",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "department",
            "department_name",
            "designation",
            "designation_name",
            "user",
            "user_email",
            "employment_type",
            "join_date",
            "end_date",
            "basic_salary",
            "address",
            "city",
            "state",
            "country",
            "notes",
            "status",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "employee_code",
            "full_name",
            "created_by",
            "created_at",
            "updated_at",
            "department_name",
            "designation_name",
            "user_email",
        )


class EmployeeCreateUpdateSerializer(serializers.Serializer):
    employee_code = serializers.CharField(
        required=False, allow_blank=True, max_length=32
    )
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=100
    )
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=20
    )
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    designation = serializers.PrimaryKeyRelatedField(queryset=Designation.objects.all())
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )
    employment_type = serializers.ChoiceField(
        choices=EmploymentType.choices,
        required=False,
        default=EmploymentType.FULL_TIME,
    )
    join_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False, allow_null=True)
    basic_salary = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal("0.00"),
        min_value=Decimal("0.00"),
    )
    address = serializers.CharField(required=False, allow_blank=True, default="")
    city = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=100
    )
    state = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=100
    )
    country = serializers.CharField(
        required=False, allow_blank=True, default="India", max_length=100
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(
        choices=EmployeeStatus.choices, required=False, default=EmployeeStatus.ACTIVE
    )
