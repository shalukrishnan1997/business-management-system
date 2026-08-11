from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.common.rbac import role_can

User = get_user_model()


def auth_header(user):
    refresh = RefreshToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}


class RoleMatrixUnitTests(APITestCase):
    def test_super_admin_can_everything(self):
        self.assertTrue(role_can(UserRole.SUPER_ADMIN, "customers", "write"))
        self.assertTrue(role_can(UserRole.SUPER_ADMIN, "audit", "read"))

    def test_viewer_read_only_customers(self):
        self.assertTrue(role_can(UserRole.VIEWER, "customers", "read"))
        self.assertFalse(role_can(UserRole.VIEWER, "customers", "write"))

    def test_sales_can_write_customers_not_inventory_adjust(self):
        self.assertTrue(role_can(UserRole.SALES_STAFF, "customers", "write"))
        self.assertFalse(role_can(UserRole.SALES_STAFF, "inventory", "write"))

    def test_inventory_can_write_products(self):
        self.assertTrue(role_can(UserRole.INVENTORY_STAFF, "products", "write"))
        self.assertFalse(role_can(UserRole.INVENTORY_STAFF, "expenses", "write"))

    def test_accountant_can_write_invoices(self):
        self.assertTrue(role_can(UserRole.ACCOUNTANT, "invoices", "write"))
        self.assertFalse(role_can(UserRole.ACCOUNTANT, "employees", "write"))


class RBACAPITests(APITestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            email="super@example.com",
            password="StrongPass123!",
            first_name="Super",
            last_name="Admin",
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
            is_superuser=True,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="StrongPass123!",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.sales = User.objects.create_user(
            email="sales@example.com",
            password="StrongPass123!",
            first_name="Sales",
            last_name="Rep",
            role=UserRole.SALES_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.viewer = User.objects.create_user(
            email="viewer@example.com",
            password="StrongPass123!",
            first_name="View",
            last_name="Only",
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE,
        )

        self.demo_url = reverse("rbac-demo-customers")
        self.perms_url = reverse("rbac-me")
        self.users_url = reverse("users-list")

    def test_viewer_can_get_customers_demo_but_not_post(self):
        self.client.credentials(**auth_header(self.viewer))
        get_resp = self.client.get(self.demo_url)
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)

        post_resp = self.client.post(self.demo_url, {}, format="json")
        self.assertEqual(post_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_sales_can_post_customers_demo(self):
        self.client.credentials(**auth_header(self.sales))
        post_resp = self.client.post(self.demo_url, {}, format="json")
        self.assertEqual(post_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(post_resp.data["success"])

    def test_my_permissions_endpoint(self):
        self.client.credentials(**auth_header(self.viewer))
        resp = self.client.get(self.perms_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["data"]["role"], UserRole.VIEWER)
        self.assertTrue(resp.data["data"]["permissions"]["customers"]["read"])
        self.assertFalse(resp.data["data"]["permissions"]["customers"]["write"])

    def test_viewer_cannot_list_users(self):
        self.client.credentials(**auth_header(self.viewer))
        resp = self.client.get(self.users_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_user_but_not_super_admin(self):
        self.client.credentials(**auth_header(self.admin))
        ok = self.client.post(
            self.users_url,
            {
                "email": "manager@example.com",
                "first_name": "New",
                "last_name": "Manager",
                "role": UserRole.MANAGER,
                "status": UserStatus.ACTIVE,
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            format="json",
        )
        self.assertEqual(ok.status_code, status.HTTP_201_CREATED)

        denied = self.client.post(
            self.users_url,
            {
                "email": "another-super@example.com",
                "first_name": "Nope",
                "last_name": "Super",
                "role": UserRole.SUPER_ADMIN,
                "status": UserStatus.ACTIVE,
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_400_BAD_REQUEST)

    def test_super_admin_can_create_super_admin(self):
        self.client.credentials(**auth_header(self.super_admin))
        resp = self.client.post(
            self.users_url,
            {
                "email": "super2@example.com",
                "first_name": "Second",
                "last_name": "Super",
                "role": UserRole.SUPER_ADMIN,
                "status": UserStatus.ACTIVE,
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["data"]["role"], UserRole.SUPER_ADMIN)

    def test_admin_list_excludes_super_admins(self):
        self.client.credentials(**auth_header(self.admin))
        resp = self.client.get(self.users_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        emails = [row["email"] for row in resp.data["results"]]
        self.assertNotIn("super@example.com", emails)
        self.assertIn("admin@example.com", emails)
