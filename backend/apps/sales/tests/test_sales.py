from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.customers.models import Customer
from apps.customers.services import get_outstanding_balance
from apps.inventory.models import StockTransaction, StockTransactionType
from apps.products.models import Category
from apps.products.services import create_product

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class SalesAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="sal-admin@example.com",
            password="StrongPass123!",
            first_name="Sal",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.sales = User.objects.create_user(
            email="sal-staff@example.com",
            password="StrongPass123!",
            first_name="Sal",
            last_name="Staff",
            role=UserRole.SALES_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.category = Category.objects.create(name="Retail")
        self.customer = Customer.objects.create(
            customer_code="CUS-8001",
            name="Walk-in Buyer",
            opening_balance=Decimal("50.00"),
            created_by=self.admin,
        )
        self.product = create_product(
            data={
                "name": "Gadget",
                "category": self.category,
                "purchase_price": Decimal("40.00"),
                "selling_price": Decimal("100.00"),
            },
            user=self.admin,
            opening_stock=Decimal("20.000"),
        )
        self.list_url = reverse("sales-list")

    def _payload(self, qty="5.000", unit_price="100.00", paid="0.00"):
        return {
            "customer": self.customer.id,
            "shipping": "10.00",
            "paid_amount": paid,
            "notes": "Test sale",
            "items": [
                {
                    "product": self.product.id,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "tax": "0.00",
                    "discount": "0.00",
                }
            ],
        }

    def test_create_complete_decreases_stock(self):
        self.client.credentials(**auth_header(self.sales))
        created = self.client.post(self.list_url, self._payload(), format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(created.data["data"]["sale_number"], "SAL-0001")
        # 5*100 + 10 shipping = 510
        self.assertEqual(created.data["data"]["grand_total"], "510.00")

        sale_id = created.data["data"]["id"]
        before = self.product.current_stock
        completed = self.client.post(reverse("sales-complete", args=[sale_id]))
        self.assertEqual(completed.status_code, status.HTTP_200_OK, completed.data)
        self.assertEqual(completed.data["data"]["status"], "completed")

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, before - Decimal("5.000"))
        self.assertTrue(
            StockTransaction.objects.filter(
                product=self.product,
                transaction_type=StockTransactionType.SALE,
                reference_id=sale_id,
            ).exists()
        )

    def test_complete_blocks_insufficient_stock(self):
        self.client.credentials(**auth_header(self.admin))
        created = self.client.post(
            self.list_url, self._payload(qty="999.000"), format="json"
        )
        sale_id = created.data["data"]["id"]
        completed = self.client.post(reverse("sales-complete", args=[sale_id]))
        self.assertEqual(completed.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("20.000"))

    def test_cancel_completed_reverses_stock(self):
        self.client.credentials(**auth_header(self.admin))
        created = self.client.post(self.list_url, self._payload(), format="json")
        sale_id = created.data["data"]["id"]
        self.client.post(reverse("sales-complete", args=[sale_id]))
        self.product.refresh_from_db()
        after_complete = self.product.current_stock

        cancelled = self.client.post(reverse("sales-cancel", args=[sale_id]))
        self.assertEqual(cancelled.status_code, status.HTTP_200_OK)
        self.assertEqual(cancelled.data["data"]["status"], "cancelled")
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, after_complete + Decimal("5.000"))
        self.assertTrue(
            StockTransaction.objects.filter(
                transaction_type=StockTransactionType.SALE_RETURN,
                reference_id=sale_id,
            ).exists()
        )

    def test_confirm_and_print(self):
        self.client.credentials(**auth_header(self.sales))
        created = self.client.post(self.list_url, self._payload(), format="json")
        sale_id = created.data["data"]["id"]
        confirmed = self.client.post(reverse("sales-confirm", args=[sale_id]))
        self.assertEqual(confirmed.status_code, status.HTTP_200_OK)
        self.assertEqual(confirmed.data["data"]["status"], "confirmed")

        printed = self.client.get(reverse("sales-print", args=[sale_id]))
        self.assertEqual(printed.status_code, status.HTTP_200_OK)
        self.assertEqual(printed.data["data"]["sale_number"], "SAL-0001")

    def test_customer_outstanding_and_sales_history(self):
        self.client.credentials(**auth_header(self.admin))
        self.client.post(
            self.list_url, self._payload(paid="100.00"), format="json"
        )
        # due = 510 - 100 = 410; opening 50 + 410 = 460
        outstanding = get_outstanding_balance(self.customer)
        self.assertEqual(outstanding, Decimal("460.00"))

        history = self.client.get(
            reverse("customers-sales-history", args=[self.customer.id])
        )
        self.assertEqual(history.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history.data["data"]["results"]), 1)
        self.assertTrue(history.data["data"]["meta"]["linked"])
