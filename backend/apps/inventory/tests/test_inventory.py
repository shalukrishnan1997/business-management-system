from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.inventory.models import StockTransaction, StockTransactionType
from apps.inventory.services import adjust_stock_out, apply_stock_movement
from apps.products.models import Category, Product
from apps.products.services import create_product

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class InventoryAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="inv-admin@example.com",
            password="StrongPass123!",
            first_name="I",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.inventory = User.objects.create_user(
            email="inv-staff@example.com",
            password="StrongPass123!",
            first_name="I",
            last_name="Staff",
            role=UserRole.INVENTORY_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.sales = User.objects.create_user(
            email="inv-sales@example.com",
            password="StrongPass123!",
            first_name="I",
            last_name="Sales",
            role=UserRole.SALES_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.category = Category.objects.create(name="Inv Cat")
        self.product = create_product(
            data={
                "name": "Widget",
                "category": self.category,
                "reorder_level": Decimal("5.000"),
            },
            user=self.admin,
            opening_stock=Decimal("10.000"),
        )

    def test_opening_stock_creates_ledger_row(self):
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("10.000"))
        txn = StockTransaction.objects.get(product=self.product)
        self.assertEqual(txn.transaction_type, StockTransactionType.OPENING)
        self.assertEqual(txn.previous_stock, Decimal("0.000"))
        self.assertEqual(txn.new_stock, Decimal("10.000"))

    def test_adjust_in_and_out_via_api(self):
        self.client.credentials(**auth_header(self.inventory))
        adjust_in = self.client.post(
            reverse("inventory-adjust-in"),
            {
                "product_id": self.product.id,
                "quantity": "5.000",
                "remarks": "Found stock",
            },
            format="json",
        )
        self.assertEqual(adjust_in.status_code, status.HTTP_201_CREATED, adjust_in.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("15.000"))

        adjust_out = self.client.post(
            reverse("inventory-adjust-out"),
            {"product_id": self.product.id, "quantity": "3.000"},
            format="json",
        )
        self.assertEqual(adjust_out.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("12.000"))

    def test_adjust_out_blocks_negative_stock(self):
        self.client.credentials(**auth_header(self.inventory))
        resp = self.client.post(
            reverse("inventory-adjust-out"),
            {"product_id": self.product.id, "quantity": "999.000"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("10.000"))

    @override_settings(ALLOW_NEGATIVE_STOCK=True)
    def test_negative_stock_allowed_when_setting_enabled(self):
        txn = adjust_stock_out(
            product=self.product, quantity=Decimal("12.000"), user=self.admin
        )
        self.assertEqual(txn.new_stock, Decimal("-2.000"))

    def test_sales_cannot_adjust_stock(self):
        self.client.credentials(**auth_header(self.sales))
        resp = self.client.post(
            reverse("inventory-adjust-in"),
            {"product_id": self.product.id, "quantity": "1.000"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_transaction_list_and_product_history(self):
        apply_stock_movement(
            product=self.product,
            transaction_type=StockTransactionType.ADJUSTMENT_IN,
            quantity=Decimal("1.000"),
            user=self.admin,
            reference_type="adjustment",
        )
        self.client.credentials(**auth_header(self.inventory))
        listed = self.client.get(
            reverse("stock-transactions-list"),
            {"product": self.product.id},
        )
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(listed.data["count"], 2)

        history = self.client.get(
            reverse("products-inventory-history", args=[self.product.id])
        )
        self.assertEqual(history.status_code, status.HTTP_200_OK)
        self.assertTrue(history.data["data"]["meta"]["linked"])
        self.assertGreaterEqual(len(history.data["data"]["results"]), 2)

    def test_low_stock_inventory_endpoint(self):
        # Drop stock below reorder
        adjust_stock_out(
            product=self.product, quantity=Decimal("6.000"), user=self.admin
        )
        self.client.credentials(**auth_header(self.inventory))
        resp = self.client.get(reverse("inventory-low-stock"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codes = [row["product_code"] for row in resp.data["data"]["results"]]
        self.assertIn(self.product.product_code, codes)
