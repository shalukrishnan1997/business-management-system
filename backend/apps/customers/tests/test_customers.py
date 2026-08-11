from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.customers.models import Customer, CustomerStatus
from apps.customers.services import generate_customer_code, get_outstanding_balance

User = get_user_model()


def auth_header(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


class CustomerAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="cust-admin@example.com",
            password="StrongPass123!",
            first_name="Cust",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.sales = User.objects.create_user(
            email="cust-sales@example.com",
            password="StrongPass123!",
            first_name="Cust",
            last_name="Sales",
            role=UserRole.SALES_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.viewer = User.objects.create_user(
            email="cust-viewer@example.com",
            password="StrongPass123!",
            first_name="Cust",
            last_name="Viewer",
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE,
        )
        self.list_url = reverse("customers-list")

    def test_generate_customer_code_sequence(self):
        self.assertEqual(generate_customer_code(), "CUS-0001")
        Customer.objects.create(
            customer_code="CUS-0001",
            name="First",
            created_by=self.admin,
        )
        self.assertEqual(generate_customer_code(), "CUS-0002")

    def test_sales_can_create_customer_with_auto_code(self):
        self.client.credentials(**auth_header(self.sales))
        resp = self.client.post(
            self.list_url,
            {
                "name": "Acme Traders",
                "company_name": "Acme Pvt Ltd",
                "email": "buyer@acme.test",
                "phone": "9876543210",
                "city": "Mumbai",
                "state": "MH",
                "credit_limit": "50000.00",
                "opening_balance": "1500.50",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["data"]["customer_code"], "CUS-0001")
        self.assertEqual(resp.data["data"]["outstanding_balance"], "1500.50")
        self.assertEqual(resp.data["data"]["created_by"], self.sales.id)

    def test_viewer_can_list_but_not_create(self):
        Customer.objects.create(
            customer_code="CUS-0009",
            name="Read Only Co",
            created_by=self.admin,
        )
        self.client.credentials(**auth_header(self.viewer))
        listed = self.client.get(self.list_url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(listed.data["count"], 1)

        created = self.client.post(
            self.list_url, {"name": "Should Fail"}, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_and_filter(self):
        Customer.objects.create(
            customer_code="CUS-0100",
            name="Alpha Stores",
            city="Pune",
            status=CustomerStatus.ACTIVE,
            created_by=self.admin,
        )
        Customer.objects.create(
            customer_code="CUS-0101",
            name="Beta Mart",
            city="Delhi",
            status=CustomerStatus.INACTIVE,
            created_by=self.admin,
        )
        self.client.credentials(**auth_header(self.admin))
        search = self.client.get(self.list_url, {"search": "Alpha"})
        self.assertEqual(search.status_code, status.HTTP_200_OK)
        self.assertEqual(search.data["count"], 1)

        filtered = self.client.get(
            self.list_url, {"status": "active", "city": "Pune"}
        )
        self.assertEqual(filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered.data["count"], 1)

    def test_update_retrieve_deactivate_activate(self):
        customer = Customer.objects.create(
            customer_code="CUS-0200",
            name="Old Name",
            phone="111",
            opening_balance=Decimal("100.00"),
            created_by=self.admin,
        )
        detail = reverse("customers-detail", args=[customer.id])
        self.client.credentials(**auth_header(self.admin))

        patched = self.client.patch(
            detail, {"name": "New Name", "phone": "222"}, format="json"
        )
        self.assertEqual(patched.status_code, status.HTTP_200_OK)
        self.assertEqual(patched.data["data"]["name"], "New Name")

        got = self.client.get(detail)
        self.assertEqual(got.status_code, status.HTTP_200_OK)
        self.assertEqual(got.data["data"]["phone"], "222")

        deleted = self.client.delete(detail)
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        customer.refresh_from_db()
        self.assertEqual(customer.status, CustomerStatus.INACTIVE)

        activated = self.client.post(reverse("customers-activate", args=[customer.id]))
        self.assertEqual(activated.status_code, status.HTTP_200_OK)
        customer.refresh_from_db()
        self.assertEqual(customer.status, CustomerStatus.ACTIVE)

    def test_outstanding_and_statement_actions(self):
        customer = Customer.objects.create(
            customer_code="CUS-0300",
            name="Balance Co",
            opening_balance=Decimal("2500.00"),
            credit_limit=Decimal("10000.00"),
            created_by=self.admin,
        )
        self.assertEqual(get_outstanding_balance(customer), Decimal("2500.00"))

        self.client.credentials(**auth_header(self.sales))
        outstanding = self.client.get(
            reverse("customers-outstanding", args=[customer.id])
        )
        self.assertEqual(outstanding.status_code, status.HTTP_200_OK)
        self.assertEqual(
            outstanding.data["data"]["outstanding_balance"], "2500.00"
        )

        statement = self.client.get(
            reverse("customers-statement", args=[customer.id])
        )
        self.assertEqual(statement.status_code, status.HTTP_200_OK)
        self.assertEqual(len(statement.data["data"]["lines"]), 1)
        self.assertEqual(
            statement.data["data"]["outstanding_balance"], "2500.00"
        )

        sales_hist = self.client.get(
            reverse("customers-sales-history", args=[customer.id])
        )
        self.assertEqual(sales_hist.status_code, status.HTTP_200_OK)
        self.assertEqual(sales_hist.data["data"]["results"], [])
