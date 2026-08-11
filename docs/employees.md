# Employees (Phase 15)

Light HR for the MVP — **not** a full payroll / attendance system.

## Models

| Model | Notes |
|-------|--------|
| **Department** | Org unit, active/inactive |
| **Designation** | Belongs to one department; unique name per department |
| **Employee** | `EMP-####`, department + designation, optional linked User |

## Rules

- Designation must belong to the employee’s department
- New employees require **active** department and designation
- Soft deactivate employees (DELETE → inactive); activate restores
- Departments/designations with children cannot be hard-deleted — deactivate instead
- Optional `user` is OneToOne — one login account per employee max
- `basic_salary` is a simple field for future reports; no payslip engine here

## Endpoints

| Base | Purpose |
|------|---------|
| `/api/v1/departments/` | CRUD + activate |
| `/api/v1/designations/` | CRUD + activate (`?department=`) |
| `/api/v1/employees/` | CRUD + activate; DELETE soft-deactivates |

## Filters (employees)

`department`, `designation`, `status`, `employment_type`, `join_from`, `join_to`, `search`

## Permissions

`CanManageEmployees` — Admin write; Manager/Viewer read (accountant has no access per RBAC).
