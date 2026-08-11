from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.employees.models import EmployeeStatus

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class EmployeeAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="emp-admin@example.com",
            password="StrongPass123!",
            first_name="Emp",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.manager = User.objects.create_user(
            email="emp-mgr@example.com",
            password="StrongPass123!",
            first_name="Emp",
            last_name="Mgr",
            role=UserRole.MANAGER,
            status=UserStatus.ACTIVE,
        )
        self.accountant = User.objects.create_user(
            email="emp-acct@example.com",
            password="StrongPass123!",
            first_name="Emp",
            last_name="Acct",
            role=UserRole.ACCOUNTANT,
            status=UserStatus.ACTIVE,
        )
        self.departments_url = reverse("departments-list")
        self.designations_url = reverse("designations-list")
        self.employees_url = reverse("employees-list")

    def test_org_and_employee_lifecycle(self):
        self.client.credentials(**auth_header(self.admin))

        dept = self.client.post(
            self.departments_url,
            {"name": "Sales", "description": "Sales team"},
            format="json",
        )
        self.assertEqual(dept.status_code, status.HTTP_201_CREATED, dept.data)
        dept_id = dept.data["data"]["id"]

        desig = self.client.post(
            self.designations_url,
            {"name": "Sales Executive", "department": dept_id},
            format="json",
        )
        self.assertEqual(desig.status_code, status.HTTP_201_CREATED, desig.data)
        desig_id = desig.data["data"]["id"]

        created = self.client.post(
            self.employees_url,
            {
                "first_name": "Riya",
                "last_name": "Shah",
                "email": "riya@example.com",
                "department": dept_id,
                "designation": desig_id,
                "basic_salary": "35000.00",
                "employment_type": "full_time",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(created.data["data"]["employee_code"], "EMP-0001")
        self.assertEqual(created.data["data"]["full_name"], "Riya Shah")
        eid = created.data["data"]["id"]

        # Wrong department/designation combo
        other_dept = self.client.post(
            self.departments_url, {"name": "Finance"}, format="json"
        )
        mismatch = self.client.post(
            self.employees_url,
            {
                "first_name": "Bad",
                "department": other_dept.data["data"]["id"],
                "designation": desig_id,
            },
            format="json",
        )
        self.assertEqual(mismatch.status_code, status.HTTP_400_BAD_REQUEST)

        deactivated = self.client.delete(reverse("employees-detail", args=[eid]))
        self.assertEqual(deactivated.status_code, status.HTTP_200_OK)
        self.assertEqual(deactivated.data["data"]["status"], EmployeeStatus.INACTIVE)

        activated = self.client.post(reverse("employees-activate", args=[eid]))
        self.assertEqual(activated.status_code, status.HTTP_200_OK)
        self.assertEqual(activated.data["data"]["status"], EmployeeStatus.ACTIVE)

    def test_manager_can_read_accountant_cannot_write(self):
        self.client.credentials(**auth_header(self.admin))
        dept = self.client.post(self.departments_url, {"name": "Ops"}, format="json")
        dept_id = dept.data["data"]["id"]
        desig = self.client.post(
            self.designations_url,
            {"name": "Coordinator", "department": dept_id},
            format="json",
        )
        desig_id = desig.data["data"]["id"]

        self.client.credentials(**auth_header(self.manager))
        listed = self.client.get(self.employees_url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)

        self.client.credentials(**auth_header(self.accountant))
        denied = self.client.post(
            self.employees_url,
            {
                "first_name": "No",
                "department": dept_id,
                "designation": desig_id,
            },
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

    def test_link_user_once_only(self):
        self.client.credentials(**auth_header(self.admin))
        dept = self.client.post(self.departments_url, {"name": "IT"}, format="json")
        dept_id = dept.data["data"]["id"]
        desig = self.client.post(
            self.designations_url,
            {"name": "Developer", "department": dept_id},
            format="json",
        )
        desig_id = desig.data["data"]["id"]

        first = self.client.post(
            self.employees_url,
            {
                "first_name": "Dev",
                "department": dept_id,
                "designation": desig_id,
                "user": self.manager.id,
            },
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED, first.data)

        second = self.client.post(
            self.employees_url,
            {
                "first_name": "Other",
                "department": dept_id,
                "designation": desig_id,
                "user": self.manager.id,
            },
            format="json",
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
