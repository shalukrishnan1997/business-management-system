"""Cross-module integration: purchase → stock → sale → invoice → payment."""
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import UserRole
from apps.common.tests.helpers import auth_header, make_user, seed_party_catalog
from apps.customers.services import get_outstanding_balance
from apps.invoices.models import InvoiceStatus
from apps.inventory.models import StockTransaction, StockTransactionType


class PurchaseSaleInvoicePaymentWorkflowTests(APITestCase):
    def setUp(self):
        self.admin = make_user(
            email="wf-admin@example.com",
            role=UserRole.ADMIN,
            is_staff=True,
            first_name="Wf",
            last_name="Admin",
        )
        seed = seed_party_catalog(user=self.admin, prefix="2301")
        self.customer = seed["customer"]
        self.supplier = seed["supplier"]
        self.product = seed["product"]

    def test_full_commercial_cycle(self):
        self.client.credentials(**auth_header(self.admin))

        # 1) Purchase draft → receive (stock in)
        purchase = self.client.post(
            reverse("purchases-list"),
            {
                "supplier": self.supplier.id,
                "discount": "0.00",
                "tax": "0.00",
                "shipping_charge": "0.00",
                "paid_amount": "0.00",
                "items": [
                    {
                        "product": self.product.id,
                        "quantity": "10.000",
                        "unit_price": "40.00",
                        "tax": "0.00",
                        "discount": "0.00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(purchase.status_code, status.HTTP_201_CREATED, purchase.data)
        purchase_id = purchase.data["data"]["id"]

        received = self.client.post(reverse("purchases-receive", args=[purchase_id]))
        self.assertEqual(received.status_code, status.HTTP_200_OK, received.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("10.000"))
        self.assertTrue(
            StockTransaction.objects.filter(
                product=self.product,
                transaction_type=StockTransactionType.PURCHASE,
                reference_id=purchase_id,
            ).exists()
        )

        # 2) Sale → complete (stock out)
        sale = self.client.post(
            reverse("sales-list"),
            {
                "customer": self.customer.id,
                "shipping": "0.00",
                "paid_amount": "0.00",
                "items": [
                    {
                        "product": self.product.id,
                        "quantity": "3.000",
                        "unit_price": "100.00",
                        "tax": "0.00",
                        "discount": "0.00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(sale.status_code, status.HTTP_201_CREATED, sale.data)
        sale_id = sale.data["data"]["id"]
        self.assertEqual(sale.data["data"]["grand_total"], "300.00")

        completed = self.client.post(reverse("sales-complete", args=[sale_id]))
        self.assertEqual(completed.status_code, status.HTTP_200_OK, completed.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, Decimal("7.000"))

        # 3) Invoice from sale
        invoice = self.client.post(
            reverse("invoices-from-sale"),
            {"sale_id": sale_id},
            format="json",
        )
        self.assertEqual(invoice.status_code, status.HTTP_201_CREATED, invoice.data)
        invoice_id = invoice.data["data"]["id"]
        self.assertEqual(invoice.data["data"]["total"], "300.00")
        self.assertEqual(invoice.data["data"]["balance"], "300.00")
        self.assertEqual(get_outstanding_balance(self.customer), Decimal("300.00"))

        sent = self.client.post(reverse("invoices-send", args=[invoice_id]))
        self.assertEqual(sent.status_code, status.HTTP_200_OK, sent.data)

        # 4) Partial then full payment
        partial = self.client.post(
            reverse("payments-list"),
            {
                "payment_type": "customer_receipt",
                "customer": self.customer.id,
                "reference_type": "invoice",
                "reference_id": invoice_id,
                "amount": "100.00",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(partial.status_code, status.HTTP_201_CREATED, partial.data)

        full = self.client.post(
            reverse("payments-list"),
            {
                "payment_type": "customer_receipt",
                "customer": self.customer.id,
                "reference_type": "invoice",
                "reference_id": invoice_id,
                "amount": "200.00",
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertEqual(full.status_code, status.HTTP_201_CREATED, full.data)

        detail = self.client.get(reverse("invoices-detail", args=[invoice_id]))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["data"]["balance"], "0.00")
        self.assertEqual(detail.data["data"]["status"], InvoiceStatus.PAID)
        self.assertEqual(get_outstanding_balance(self.customer), Decimal("0.00"))
