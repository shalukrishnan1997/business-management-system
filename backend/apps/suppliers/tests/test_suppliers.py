from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.suppliers.models import Supplier, SupplierStatus
from apps.suppliers.services import generate_supplier_code, get_outstanding_balance

User = get_user_model()


def auth_header(user):
    token = RefreshToken.for_user(user).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


class SupplierAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="sup-admin@example.com",
            password="StrongPass123!",
            first_name="Sup",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.inventory = User.objects.create_user(
            email="sup-inv@example.com",
            password="StrongPass123!",
            first_name="Sup",
            last_name="Inventory",
            role=UserRole.INVENTORY_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.sales = User.objects.create_user(
            email="sup-sales@example.com",
            password="StrongPass123!",
            first_name="Sup",
            last_name="Sales",
            role=UserRole.SALES_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.viewer = User.objects.create_user(
            email="sup-viewer@example.com",
            password="StrongPass123!",
            first_name="Sup",
            last_name="Viewer",
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE,
        )
        self.list_url = reverse("suppliers-list")

    def test_generate_supplier_code_sequence(self):
        self.assertEqual(generate_supplier_code(), "SUP-0001")
        Supplier.objects.create(
            supplier_code="SUP-0001",
            name="First Vendor",
            created_by=self.admin,
        )
        self.assertEqual(generate_supplier_code(), "SUP-0002")

    def test_inventory_can_create_supplier_with_auto_code(self):
        self.client.credentials(**auth_header(self.inventory))
        resp = self.client.post(
            self.list_url,
            {
                "name": "Global Parts",
                "company_name": "Global Parts Ltd",
                "email": "sales@globalparts.test",
                "phone": "9123456780",
                "city": "Chennai",
                "opening_balance": "3200.00",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["data"]["supplier_code"], "SUP-0001")
        self.assertEqual(resp.data["data"]["outstanding_balance"], "3200.00")
        self.assertEqual(resp.data["data"]["created_by"], self.inventory.id)

    def test_sales_can_read_but_not_write_suppliers(self):
        Supplier.objects.create(
            supplier_code="SUP-0009",
            name="Read Vendor",
            created_by=self.admin,
        )
        self.client.credentials(**auth_header(self.sales))
        listed = self.client.get(self.list_url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)

        created = self.client.post(
            self.list_url, {"name": "Should Fail"}, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_can_list_but_not_create(self):
        Supplier.objects.create(
            supplier_code="SUP-0010",
            name="Viewer Vendor",
            created_by=self.admin,
        )
        self.client.credentials(**auth_header(self.viewer))
        listed = self.client.get(self.list_url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)

        created = self.client.post(
            self.list_url, {"name": "Nope"}, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_and_filter(self):
        Supplier.objects.create(
            supplier_code="SUP-0100",
            name="Alpha Supplies",
            city="Pune",
            status=SupplierStatus.ACTIVE,
            created_by=self.admin,
        )
        Supplier.objects.create(
            supplier_code="SUP-0101",
            name="Beta Wholesale",
            city="Delhi",
            status=SupplierStatus.INACTIVE,
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

    def test_update_deactivate_activate(self):
        supplier = Supplier.objects.create(
            supplier_code="SUP-0200",
            name="Old Vendor",
            phone="111",
            created_by=self.admin,
        )
        detail = reverse("suppliers-detail", args=[supplier.id])
        self.client.credentials(**auth_header(self.admin))

        patched = self.client.patch(
            detail, {"name": "New Vendor", "phone": "222"}, format="json"
        )
        self.assertEqual(patched.status_code, status.HTTP_200_OK)
        self.assertEqual(patched.data["data"]["name"], "New Vendor")

        deleted = self.client.delete(detail)
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        supplier.refresh_from_db()
        self.assertEqual(supplier.status, SupplierStatus.INACTIVE)

        activated = self.client.post(
            reverse("suppliers-activate", args=[supplier.id])
        )
        self.assertEqual(activated.status_code, status.HTTP_200_OK)
        supplier.refresh_from_db()
        self.assertEqual(supplier.status, SupplierStatus.ACTIVE)

    def test_outstanding_statement_and_histories(self):
        supplier = Supplier.objects.create(
            supplier_code="SUP-0300",
            name="Balance Vendor",
            opening_balance=Decimal("4500.00"),
            created_by=self.admin,
        )
        self.assertEqual(get_outstanding_balance(supplier), Decimal("4500.00"))

        self.client.credentials(**auth_header(self.inventory))
        outstanding = self.client.get(
            reverse("suppliers-outstanding", args=[supplier.id])
        )
        self.assertEqual(outstanding.status_code, status.HTTP_200_OK)
        self.assertEqual(
            outstanding.data["data"]["outstanding_balance"], "4500.00"
        )

        statement = self.client.get(
            reverse("suppliers-statement", args=[supplier.id])
        )
        self.assertEqual(statement.status_code, status.HTTP_200_OK)
        self.assertEqual(len(statement.data["data"]["lines"]), 1)

        purchases = self.client.get(
            reverse("suppliers-purchase-history", args=[supplier.id])
        )
        self.assertEqual(purchases.status_code, status.HTTP_200_OK)
        self.assertEqual(purchases.data["data"]["results"], [])

        payments = self.client.get(
            reverse("suppliers-payment-history", args=[supplier.id])
        )
        self.assertEqual(payments.status_code, status.HTTP_200_OK)
        self.assertEqual(payments.data["data"]["results"], [])
