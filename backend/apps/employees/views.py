from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import CanManageEmployees, IsAuthenticatedAndActive
from apps.common.responses import success_response

from .filters import DepartmentFilter, DesignationFilter, EmployeeFilter
from .models import Department, Designation, Employee
from .serializers import (
    DepartmentSerializer,
    DesignationSerializer,
    EmployeeCreateUpdateSerializer,
    EmployeeSerializer,
)
from .services import (
    activate_department,
    activate_designation,
    activate_employee,
    create_employee,
    deactivate_department,
    deactivate_designation,
    deactivate_employee,
    update_employee,
)


@extend_schema_view(
    list=extend_schema(tags=["Departments"]),
    retrieve=extend_schema(tags=["Departments"]),
    create=extend_schema(tags=["Departments"]),
    update=extend_schema(tags=["Departments"]),
    partial_update=extend_schema(tags=["Departments"]),
    destroy=extend_schema(tags=["Departments"]),
)
class DepartmentViewSet(viewsets.ModelViewSet):
    module = "employees"
    permission_classes = [IsAuthenticatedAndActive, CanManageEmployees]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DepartmentFilter
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        return Department.objects.annotate(
            designations_count=Count("designations", distinct=True),
            employees_count=Count("employees", distinct=True),
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(
            data=self.get_serializer(self.get_object()).data,
            message="Department retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = serializer.save()
        department = self.get_queryset().get(pk=department.pk)
        return success_response(
            data=self.get_serializer(department).data,
            message="Department created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        department = self.get_object()
        serializer = self.get_serializer(department, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        department = self.get_queryset().get(pk=department.pk)
        return success_response(
            data=self.get_serializer(department).data,
            message="Department updated.",
        )

    def destroy(self, request, *args, **kwargs):
        department = self.get_object()
        if department.designations.exists() or department.employees.exists():
            return Response(
                {
                    "success": False,
                    "message": (
                        "Cannot delete a department with designations or employees. "
                        "Deactivate it instead."
                    ),
                    "errors": {"detail": ["Department has related records."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        deactivate_department(department)
        return success_response(message="Department deactivated.")

    @extend_schema(tags=["Departments"])
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        department = activate_department(self.get_object())
        department = self.get_queryset().get(pk=department.pk)
        return success_response(
            data=self.get_serializer(department).data,
            message="Department activated.",
        )


@extend_schema_view(
    list=extend_schema(tags=["Designations"]),
    retrieve=extend_schema(tags=["Designations"]),
    create=extend_schema(tags=["Designations"]),
    update=extend_schema(tags=["Designations"]),
    partial_update=extend_schema(tags=["Designations"]),
    destroy=extend_schema(tags=["Designations"]),
)
class DesignationViewSet(viewsets.ModelViewSet):
    module = "employees"
    permission_classes = [IsAuthenticatedAndActive, CanManageEmployees]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DesignationFilter
    search_fields = ["name", "description", "department__name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]
    serializer_class = DesignationSerializer

    def get_queryset(self):
        return Designation.objects.select_related("department").annotate(
            employees_count=Count("employees")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(
            data=self.get_serializer(self.get_object()).data,
            message="Designation retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        designation = serializer.save()
        designation = self.get_queryset().get(pk=designation.pk)
        return success_response(
            data=self.get_serializer(designation).data,
            message="Designation created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        designation = self.get_object()
        serializer = self.get_serializer(
            designation, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        designation = self.get_queryset().get(pk=designation.pk)
        return success_response(
            data=self.get_serializer(designation).data,
            message="Designation updated.",
        )

    def destroy(self, request, *args, **kwargs):
        designation = self.get_object()
        if designation.employees.exists():
            return Response(
                {
                    "success": False,
                    "message": (
                        "Cannot delete a designation with employees. "
                        "Deactivate it instead."
                    ),
                    "errors": {"detail": ["Designation has related employees."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        deactivate_designation(designation)
        return success_response(message="Designation deactivated.")

    @extend_schema(tags=["Designations"])
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        designation = activate_designation(self.get_object())
        designation = self.get_queryset().get(pk=designation.pk)
        return success_response(
            data=self.get_serializer(designation).data,
            message="Designation activated.",
        )


@extend_schema_view(
    list=extend_schema(tags=["Employees"]),
    retrieve=extend_schema(tags=["Employees"]),
    create=extend_schema(tags=["Employees"]),
    update=extend_schema(tags=["Employees"]),
    partial_update=extend_schema(tags=["Employees"]),
    destroy=extend_schema(tags=["Employees"]),
)
class EmployeeViewSet(viewsets.ModelViewSet):
    module = "employees"
    permission_classes = [IsAuthenticatedAndActive, CanManageEmployees]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EmployeeFilter
    search_fields = [
        "employee_code",
        "first_name",
        "last_name",
        "email",
        "phone",
        "department__name",
        "designation__name",
    ]
    ordering_fields = [
        "first_name",
        "last_name",
        "join_date",
        "employee_code",
        "created_at",
    ]
    ordering = ["first_name", "last_name"]

    def get_queryset(self):
        return Employee.objects.select_related(
            "department", "designation", "user", "created_by"
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return EmployeeCreateUpdateSerializer
        return EmployeeSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = EmployeeSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(
            data=EmployeeSerializer(self.get_object(), context={"request": request}).data,
            message="Employee retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = create_employee(
            data=dict(serializer.validated_data), user=request.user
        )
        employee = self.get_queryset().get(pk=employee.pk)
        return success_response(
            data=EmployeeSerializer(employee, context={"request": request}).data,
            message="Employee created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        employee = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        employee = update_employee(
            employee=employee, data=dict(serializer.validated_data)
        )
        employee = self.get_queryset().get(pk=employee.pk)
        return success_response(
            data=EmployeeSerializer(employee, context={"request": request}).data,
            message="Employee updated.",
        )

    def destroy(self, request, *args, **kwargs):
        employee = deactivate_employee(self.get_object())
        return success_response(
            data=EmployeeSerializer(employee, context={"request": request}).data,
            message="Employee deactivated.",
        )

    @extend_schema(tags=["Employees"])
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        employee = activate_employee(self.get_object())
        employee = self.get_queryset().get(pk=employee.pk)
        return success_response(
            data=EmployeeSerializer(employee, context={"request": request}).data,
            message="Employee activated.",
        )
