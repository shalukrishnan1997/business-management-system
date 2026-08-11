import django_filters

from .models import (
    Department,
    Designation,
    Employee,
    EmployeeStatus,
    EmploymentType,
    OrgUnitStatus,
)


class DepartmentFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=OrgUnitStatus.choices)

    class Meta:
        model = Department
        fields = ["status"]


class DesignationFilter(django_filters.FilterSet):
    department = django_filters.NumberFilter(field_name="department_id")
    status = django_filters.ChoiceFilter(choices=OrgUnitStatus.choices)

    class Meta:
        model = Designation
        fields = ["department", "status"]


class EmployeeFilter(django_filters.FilterSet):
    department = django_filters.NumberFilter(field_name="department_id")
    designation = django_filters.NumberFilter(field_name="designation_id")
    status = django_filters.ChoiceFilter(choices=EmployeeStatus.choices)
    employment_type = django_filters.ChoiceFilter(choices=EmploymentType.choices)
    join_from = django_filters.DateFilter(field_name="join_date", lookup_expr="gte")
    join_to = django_filters.DateFilter(field_name="join_date", lookup_expr="lte")

    class Meta:
        model = Employee
        fields = ["department", "designation", "status", "employment_type"]
