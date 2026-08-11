from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.inventory.models import StockTransaction, StockTransactionType
from apps.products.models import Category, Product
from apps.products.services import create_product
from apps.purchases.models import PurchaseStatus
from apps.suppliers.models import Supplier
from apps.suppliers.services import get_outstanding_balance

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class PurchaseAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="pur-admin@example.com",
            password="StrongPass123!",
            first_name="Pur",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.inventory = User.objects.create_user(
            email="pur-inv@example.com",
            password="StrongPass123!",
            first_name="Pur",
            last_name="Inv",
            role=UserRole.INVENTORY_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.category = Category.objects.create(name="Raw")
        self.supplier = Supplier.objects.create(
            supplier_code="SUP-7001",
            name="Steel Co",
            opening_balance=Decimal("100.00"),
            created_by=self.admin,
        )
        self.product = create_product(
            data={
                "name": "Steel Rod",
                "category": self.category,
                "purchase_price": Decimal("50.00"),
                "selling_price": Decimal("80.00"),
            },
            user=self.admin,
            opening_stock=Decimal("5.000"),
        )
        self.list_url = reverse("purchases-list")

    def _payload(self, qty="10.000", unit_price="50.00", paid="0.00"):
        return {
            "supplier": self.supplier.id,
            "reference_number": "PO-REF-1",
            "discount": "0.00",
            "tax": "0.00",
            "shipping_charge": "20.00",
            "paid_amount": paid,
            "notes": "Test PO",
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

    def test_create_draft_receive_increases_stock(self):
        self.client.credentials(**auth_header(self.inventory))
        created = self.client.post(self.list_url, self._payload(), format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(created.data["data"]["purchase_number"], "PUR-0001")
        self.assertEqual(created.data["data"]["purchase_status"], "draft")
        # 10*50 + 20 shipping = 520
        self.assertEqual(created.data["data"]["grand_total"], "520.00")
        self.assertEqual(created.data["data"]["due_amount"], "520.00")

        purchase_id = created.data["data"]["id"]
        before = self.product.current_stock
        received = self.client.post(reverse("purchases-receive", args=[purchase_id]))
        self.assertEqual(received.status_code, status.HTTP_200_OK, received.data)
        self.assertEqual(received.data["data"]["purchase_status"], "received")

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, before + Decimal("10.000"))
        self.assertTrue(
            StockTransaction.objects.filter(
                product=self.product,
                transaction_type=StockTransactionType.PURCHASE,
                reference_id=purchase_id,
            ).exists()
        )

    def test_cancel_received_reverses_stock(self):
        self.client.credentials(**auth_header(self.admin))
        created = self.client.post(self.list_url, self._payload(), format="json")
        purchase_id = created.data["data"]["id"]
        self.client.post(reverse("purchases-receive", args=[purchase_id]))
        self.product.refresh_from_db()
        stock_after_receive = self.product.current_stock

        cancelled = self.client.post(reverse("purchases-cancel", args=[purchase_id]))
        self.assertEqual(cancelled.status_code, status.HTTP_200_OK)
        self.assertEqual(cancelled.data["data"]["purchase_status"], "cancelled")
        self.product.refresh_from_db()
        self.assertEqual(
            self.product.current_stock, stock_after_receive - Decimal("10.000")
        )
        self.assertTrue(
            StockTransaction.objects.filter(
                transaction_type=StockTransactionType.PURCHASE_RETURN,
                reference_id=purchase_id,
            ).exists()
        )

    def test_cannot_edit_after_received(self):
        self.client.credentials(**auth_header(self.admin))
        created = self.client.post(self.list_url, self._payload(), format="json")
        purchase_id = created.data["data"]["id"]
        self.client.post(reverse("purchases-receive", args=[purchase_id]))
        updated = self.client.patch(
            reverse("purchases-detail", args=[purchase_id]),
            {"notes": "nope"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mark_ordered_and_print(self):
        self.client.credentials(**auth_header(self.admin))
        created = self.client.post(self.list_url, self._payload(), format="json")
        purchase_id = created.data["data"]["id"]
        ordered = self.client.post(
            reverse("purchases-mark-ordered", args=[purchase_id])
        )
        self.assertEqual(ordered.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered.data["data"]["purchase_status"], "ordered")

        printed = self.client.get(reverse("purchases-print", args=[purchase_id]))
        self.assertEqual(printed.status_code, status.HTTP_200_OK)
        self.assertEqual(printed.data["data"]["purchase_number"], "PUR-0001")
        self.assertEqual(len(printed.data["data"]["items"]), 1)

    def test_supplier_outstanding_includes_purchase_due(self):
        self.client.credentials(**auth_header(self.admin))
        self.client.post(
            self.list_url, self._payload(paid="100.00"), format="json"
        )
        # due = 520 - 100 = 420; opening 100 + 420 = 520
        outstanding = get_outstanding_balance(self.supplier)
        self.assertEqual(outstanding, Decimal("520.00"))

        history = self.client.get(
            reverse("suppliers-purchase-history", args=[self.supplier.id])
        )
        self.assertEqual(history.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history.data["data"]["results"]), 1)
        self.assertTrue(history.data["data"]["meta"]["linked"])
