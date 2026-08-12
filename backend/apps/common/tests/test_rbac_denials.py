"""HTTP-level RBAC denial smoke tests for core mutating endpoints."""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import UserRole
from apps.common.tests.helpers import auth_header, make_user, seed_party_catalog


class RbacDenialAPITests(APITestCase):
    def setUp(self):
        self.admin = make_user(
            email="rbac-admin@example.com",
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.viewer = make_user(
            email="rbac-viewer@example.com",
            role=UserRole.VIEWER,
            first_name="View",
        )
        self.sales = make_user(
            email="rbac-sales@example.com",
            role=UserRole.SALES_STAFF,
            first_name="Sales",
        )
        self.inventory = make_user(
            email="rbac-inv@example.com",
            role=UserRole.INVENTORY_STAFF,
            first_name="Inv",
        )
        seed = seed_party_catalog(user=self.admin, prefix="RBAC")
        self.customer = seed["customer"]
        self.supplier = seed["supplier"]
        self.product = seed["product"]

    def test_viewer_cannot_write_sales_or_invoices(self):
        self.client.credentials(**auth_header(self.viewer))
        sale = self.client.post(
            reverse("sales-list"),
            {
                "customer": self.customer.id,
                "shipping": "0.00",
                "paid_amount": "0.00",
                "items": [
                    {
                        "product": self.product.id,
                        "quantity": "1.000",
                        "unit_price": "100.00",
                        "tax": "0.00",
                        "discount": "0.00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(sale.status_code, status.HTTP_403_FORBIDDEN)

        invoice = self.client.post(
            reverse("invoices-list"),
            {
                "customer": self.customer.id,
                "items": [
                    {
                        "product": self.product.id,
                        "quantity": "1.000",
                        "unit_price": "100.00",
                        "discount": "0.00",
                        "tax": "0.00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(invoice.status_code, status.HTTP_403_FORBIDDEN)

        payment = self.client.post(
            reverse("payments-list"),
            {
                "payment_type": "customer_receipt",
                "customer": self.customer.id,
                "amount": "10.00",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(payment.status_code, status.HTTP_403_FORBIDDEN)

    def test_sales_cannot_write_purchases(self):
        self.client.credentials(**auth_header(self.sales))
        purchase = self.client.post(
            reverse("purchases-list"),
            {
                "supplier": self.supplier.id,
                "items": [
                    {
                        "product": self.product.id,
                        "quantity": "1.000",
                        "unit_price": "40.00",
                        "tax": "0.00",
                        "discount": "0.00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(purchase.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_cannot_write_invoices(self):
        self.client.credentials(**auth_header(self.inventory))
        invoice = self.client.post(
            reverse("invoices-list"),
            {
                "customer": self.customer.id,
                "items": [
                    {
                        "product": self.product.id,
                        "quantity": "1.000",
                        "unit_price": "100.00",
                        "discount": "0.00",
                        "tax": "0.00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(invoice.status_code, status.HTTP_403_FORBIDDEN)
