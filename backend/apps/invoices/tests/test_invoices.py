from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.customers.models import Customer
from apps.customers.services import get_outstanding_balance
from apps.invoices.models import InvoiceStatus
from apps.products.models import Category
from apps.products.services import create_product
from apps.sales.services import create_sale

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class InvoiceAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="inv-admin@example.com",
            password="StrongPass123!",
            first_name="Inv",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.accountant = User.objects.create_user(
            email="inv-acct@example.com",
            password="StrongPass123!",
            first_name="Inv",
            last_name="Acct",
            role=UserRole.ACCOUNTANT,
            status=UserStatus.ACTIVE,
        )
        self.category = Category.objects.create(name="Inv Cat")
        self.customer = Customer.objects.create(
            customer_code="CUS-9101",
            name="Invoice Customer",
            email="buyer@invoice.test",
            opening_balance=Decimal("100.00"),
            created_by=self.admin,
        )
        self.product = create_product(
            data={
                "name": "Invoiced Item",
                "category": self.category,
                "selling_price": Decimal("50.00"),
            },
            user=self.admin,
            opening_stock=Decimal("100.000"),
        )
        self.list_url = reverse("invoices-list")

    def _payload(self):
        return {
            "customer": self.customer.id,
            "discount": "0.00",
            "tax": "0.00",
            "notes": "Test invoice",
            "items": [
                {
                    "product": self.product.id,
                    "quantity": "2.000",
                    "unit_price": "50.00",
                    "discount": "0.00",
                    "tax": "0.00",
                }
            ],
        }

    def test_create_send_pdf_and_email(self):
        self.client.credentials(**auth_header(self.accountant))
        created = self.client.post(self.list_url, self._payload(), format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(created.data["data"]["invoice_number"], "INV-0001")
        self.assertEqual(created.data["data"]["total"], "100.00")
        self.assertEqual(created.data["data"]["balance"], "100.00")
        iid = created.data["data"]["id"]

        sent = self.client.post(reverse("invoices-send", args=[iid]))
        self.assertEqual(sent.status_code, status.HTTP_200_OK)
        self.assertEqual(sent.data["data"]["status"], InvoiceStatus.SENT)

        pdf = self.client.get(reverse("invoices-pdf", args=[iid]))
        self.assertEqual(pdf.status_code, status.HTTP_200_OK)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))

        emailed = self.client.post(reverse("invoices-email", args=[iid]), {}, format="json")
        self.assertEqual(emailed.status_code, status.HTTP_200_OK, emailed.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_from_sale_and_outstanding_no_double_count(self):
        self.client.credentials(**auth_header(self.admin))
        sale = create_sale(
            data={
                "customer": self.customer,
                "paid_amount": Decimal("0.00"),
                "shipping": Decimal("0.00"),
                "notes": "",
            },
            items_data=[
                {
                    "product": self.product,
                    "quantity": Decimal("4.000"),
                    "unit_price": Decimal("50.00"),
                    "tax": Decimal("0.00"),
                    "discount": Decimal("0.00"),
                }
            ],
            user=self.admin,
        )
        # Uninvoiced: opening 100 + sale due 200 = 300
        self.assertEqual(get_outstanding_balance(self.customer), Decimal("300.00"))

        created = self.client.post(
            reverse("invoices-from-sale"),
            {"sale_id": sale.id, "due_days": 7},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(created.data["data"]["total"], "200.00")
        self.assertEqual(created.data["data"]["related_sale"], sale.id)
        # After invoice: opening 100 + invoice balance 200 (sale excluded) = 300
        self.assertEqual(get_outstanding_balance(self.customer), Decimal("300.00"))

        history = self.client.get(
            reverse("customers-invoice-history", args=[self.customer.id])
        )
        self.assertEqual(history.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history.data["data"]["results"]), 1)
        self.assertTrue(history.data["data"]["meta"]["linked"])

    def test_mark_overdue(self):
        self.client.credentials(**auth_header(self.admin))
        created = self.client.post(self.list_url, self._payload(), format="json")
        iid = created.data["data"]["id"]
        self.client.post(reverse("invoices-send", args=[iid]))

        from apps.invoices.models import Invoice

        inv = Invoice.objects.get(pk=iid)
        inv.due_date = timezone.localdate() - timedelta(days=1)
        inv.save(update_fields=["due_date"])

        result = self.client.post(reverse("invoices-mark-overdue"))
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(result.data["data"]["updated"], 1)
        inv.refresh_from_db()
        self.assertEqual(inv.status, InvoiceStatus.OVERDUE)

    def test_cancel_invoice_and_block_paid_cancel(self):
        self.client.credentials(**auth_header(self.accountant))
        created = self.client.post(self.list_url, self._payload(), format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        iid = created.data["data"]["id"]

        cancelled = self.client.post(reverse("invoices-cancel", args=[iid]))
        self.assertEqual(cancelled.status_code, status.HTTP_200_OK, cancelled.data)
        self.assertEqual(cancelled.data["data"]["status"], InvoiceStatus.CANCELLED)

        again = self.client.post(reverse("invoices-cancel", args=[iid]))
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

        # Paid invoice cannot be cancelled
        paid_invoice = self.client.post(self.list_url, self._payload(), format="json")
        paid_id = paid_invoice.data["data"]["id"]
        from apps.invoices.models import Invoice

        inv = Invoice.objects.get(pk=paid_id)
        inv.paid_amount = inv.total
        inv.balance = Decimal("0.00")
        inv.status = InvoiceStatus.PAID
        inv.save(update_fields=["paid_amount", "balance", "status", "updated_at"])

        blocked = self.client.post(reverse("invoices-cancel", args=[paid_id]))
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)
