from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.products.models import Category, Product, ProductStatus
from apps.products.services import generate_product_code, low_stock_queryset
from apps.suppliers.models import Supplier

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class ProductAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="prd-admin@example.com",
            password="StrongPass123!",
            first_name="P",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.inventory = User.objects.create_user(
            email="prd-inv@example.com",
            password="StrongPass123!",
            first_name="P",
            last_name="Inv",
            role=UserRole.INVENTORY_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.sales = User.objects.create_user(
            email="prd-sales@example.com",
            password="StrongPass123!",
            first_name="P",
            last_name="Sales",
            role=UserRole.SALES_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.category = Category.objects.create(name="Electronics")
        self.supplier = Supplier.objects.create(
            supplier_code="SUP-9001",
            name="Tech Vendor",
            created_by=self.admin,
        )
        self.products_url = reverse("products-list")
        self.categories_url = reverse("categories-list")

    def test_generate_product_code(self):
        self.assertEqual(generate_product_code(), "PRD-0001")

    def test_create_category_and_product_with_opening_stock(self):
        self.client.credentials(**auth_header(self.inventory))
        cat = self.client.post(
            self.categories_url,
            {"name": "Stationery", "description": "Office supplies"},
            format="json",
        )
        self.assertEqual(cat.status_code, status.HTTP_201_CREATED, cat.data)
        category_id = cat.data["data"]["id"]

        prod = self.client.post(
            self.products_url,
            {
                "name": "Notebook A5",
                "category": category_id,
                "barcode": "8901001001",
                "purchase_price": "20.00",
                "selling_price": "35.00",
                "tax_percentage": "18.00",
                "minimum_stock": "10",
                "reorder_level": "15",
                "supplier": self.supplier.id,
                "opening_stock": "12.000",
            },
            format="json",
        )
        self.assertEqual(prod.status_code, status.HTTP_201_CREATED, prod.data)
        self.assertEqual(prod.data["data"]["product_code"], "PRD-0001")
        self.assertEqual(prod.data["data"]["current_stock"], "12.000")
        self.assertTrue(prod.data["data"]["is_low_stock"])

    def test_sales_can_read_but_not_write_products(self):
        Product.objects.create(
            product_code="PRD-0100",
            name="Read Only Item",
            category=self.category,
            created_by=self.admin,
        )
        self.client.credentials(**auth_header(self.sales))
        listed = self.client.get(self.products_url)
        self.assertEqual(listed.status_code, status.HTTP_200_OK)

        created = self.client.post(
            self.products_url, {"name": "Nope"}, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_403_FORBIDDEN)

    def test_current_stock_not_changed_via_update(self):
        product = Product.objects.create(
            product_code="PRD-0200",
            name="Stock Guard",
            category=self.category,
            current_stock=Decimal("50.000"),
            created_by=self.admin,
        )
        self.client.credentials(**auth_header(self.admin))
        resp = self.client.patch(
            reverse("products-detail", args=[product.id]),
            {"name": "Stock Guard Updated", "current_stock": "1.000"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.name, "Stock Guard Updated")
        self.assertEqual(product.current_stock, Decimal("50.000"))

    def test_low_stock_filter_and_endpoint(self):
        Product.objects.create(
            product_code="PRD-0300",
            name="Low Item",
            category=self.category,
            current_stock=Decimal("2.000"),
            reorder_level=Decimal("5.000"),
            created_by=self.admin,
        )
        Product.objects.create(
            product_code="PRD-0301",
            name="OK Item",
            category=self.category,
            current_stock=Decimal("100.000"),
            reorder_level=Decimal("5.000"),
            created_by=self.admin,
        )
        self.assertEqual(low_stock_queryset().count(), 1)

        self.client.credentials(**auth_header(self.inventory))
        filtered = self.client.get(self.products_url, {"low_stock": "true"})
        self.assertEqual(filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(filtered.data["count"], 1)

        endpoint = self.client.get(reverse("products-low-stock"))
        self.assertEqual(endpoint.status_code, status.HTTP_200_OK)
        self.assertEqual(endpoint.data["count"], 1)

    def test_sku_and_barcode_lookup(self):
        Product.objects.create(
            product_code="PRD-0400",
            barcode="BAR-999",
            name="Lookup Item",
            category=self.category,
            created_by=self.admin,
        )
        self.client.credentials(**auth_header(self.admin))
        by_sku = self.client.get(reverse("products-lookup"), {"sku": "PRD-0400"})
        self.assertEqual(by_sku.status_code, status.HTTP_200_OK)
        self.assertEqual(by_sku.data["data"]["name"], "Lookup Item")

        by_barcode = self.client.get(
            reverse("products-lookup"), {"barcode": "BAR-999"}
        )
        self.assertEqual(by_barcode.status_code, status.HTTP_200_OK)

    def test_price_update_and_deactivate(self):
        product = Product.objects.create(
            product_code="PRD-0500",
            name="Priced Item",
            category=self.category,
            purchase_price=Decimal("10.00"),
            selling_price=Decimal("15.00"),
            created_by=self.admin,
        )
        self.client.credentials(**auth_header(self.admin))
        prices = self.client.patch(
            reverse("products-prices", args=[product.id]),
            {"selling_price": "18.50", "tax_percentage": "12.00"},
            format="json",
        )
        self.assertEqual(prices.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.selling_price, Decimal("18.50"))

        deleted = self.client.delete(reverse("products-detail", args=[product.id]))
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.status, ProductStatus.INACTIVE)

    def test_filter_by_category(self):
        other = Category.objects.create(name="Furniture")
        Product.objects.create(
            product_code="PRD-0600",
            name="Phone",
            category=self.category,
            created_by=self.admin,
        )
        Product.objects.create(
            product_code="PRD-0601",
            name="Chair",
            category=other,
            created_by=self.admin,
        )
        self.client.credentials(**auth_header(self.admin))
        resp = self.client.get(
            self.products_url, {"category": self.category.id}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["name"], "Phone")
