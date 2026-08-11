from django.contrib import admin

from .models import Department, Designation, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "description")


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "status", "created_at")
    list_filter = ("status", "department")
    search_fields = ("name", "department__name")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_code",
        "first_name",
        "last_name",
        "department",
        "designation",
        "employment_type",
        "status",
        "join_date",
    )
    list_filter = ("status", "employment_type", "department")
    search_fields = ("employee_code", "first_name", "last_name", "email", "phone")
    readonly_fields = ("employee_code", "created_at", "updated_at", "created_by")
