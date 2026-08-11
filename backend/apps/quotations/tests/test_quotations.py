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
from apps.products.models import Category
from apps.products.services import create_product
from apps.quotations.models import QuotationStatus
from apps.sales.models import SalesOrder

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class QuotationAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="qtn-admin@example.com",
            password="StrongPass123!",
            first_name="Q",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.sales = User.objects.create_user(
            email="qtn-sales@example.com",
            password="StrongPass123!",
            first_name="Q",
            last_name="Sales",
            role=UserRole.SALES_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.category = Category.objects.create(name="Quote Cat")
        self.customer = Customer.objects.create(
            customer_code="CUS-9001",
            name="Quote Customer",
            email="buyer@quote.test",
            created_by=self.admin,
        )
        self.product = create_product(
            data={
                "name": "Quoted Item",
                "category": self.category,
                "selling_price": Decimal("200.00"),
            },
            user=self.admin,
            opening_stock=Decimal("50.000"),
        )
        self.list_url = reverse("quotations-list")

    def _payload(self):
        return {
            "customer": self.customer.id,
            "valid_until": (timezone.localdate() + timedelta(days=14)).isoformat(),
            "discount": "0.00",
            "tax": "0.00",
            "notes": "Promo quote",
            "items": [
                {
                    "product": self.product.id,
                    "quantity": "2.000",
                    "unit_price": "200.00",
                    "discount": "0.00",
                    "tax": "0.00",
                }
            ],
        }

    def test_create_send_accept_convert_to_sale(self):
        self.client.credentials(**auth_header(self.sales))
        created = self.client.post(self.list_url, self._payload(), format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(created.data["data"]["quotation_number"], "QTN-0001")
        self.assertEqual(created.data["data"]["grand_total"], "400.00")
        qid = created.data["data"]["id"]

        sent = self.client.post(reverse("quotations-send", args=[qid]))
        self.assertEqual(sent.status_code, status.HTTP_200_OK)
        self.assertEqual(sent.data["data"]["status"], QuotationStatus.SENT)

        accepted = self.client.post(reverse("quotations-accept", args=[qid]))
        self.assertEqual(accepted.status_code, status.HTTP_200_OK)
        self.assertEqual(accepted.data["data"]["status"], QuotationStatus.ACCEPTED)

        converted = self.client.post(
            reverse("quotations-convert-to-sale", args=[qid])
        )
        self.assertEqual(converted.status_code, status.HTTP_201_CREATED, converted.data)
        self.assertEqual(converted.data["data"]["sale"]["sale_number"], "SAL-0001")
        self.assertEqual(converted.data["data"]["sale"]["grand_total"], "400.00")
        self.assertTrue(
            SalesOrder.objects.filter(sale_number="SAL-0001").exists()
        )

        again = self.client.post(reverse("quotations-convert-to-sale", args=[qid]))
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_quotation(self):
        self.client.credentials(**auth_header(self.admin))
        created = self.client.post(self.list_url, self._payload(), format="json")
        qid = created.data["data"]["id"]
        self.client.post(reverse("quotations-send", args=[qid]))
        rejected = self.client.post(reverse("quotations-reject", args=[qid]))
        self.assertEqual(rejected.status_code, status.HTTP_200_OK)
        self.assertEqual(rejected.data["data"]["status"], QuotationStatus.REJECTED)

    def test_pdf_and_email(self):
        self.client.credentials(**auth_header(self.admin))
        created = self.client.post(self.list_url, self._payload(), format="json")
        qid = created.data["data"]["id"]

        pdf = self.client.get(reverse("quotations-pdf", args=[qid]))
        self.assertEqual(pdf.status_code, status.HTTP_200_OK)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))

        emailed = self.client.post(
            reverse("quotations-email", args=[qid]), {}, format="json"
        )
        self.assertEqual(emailed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("QTN-0001", mail.outbox[0].subject)
        self.assertEqual(len(mail.outbox[0].attachments), 1)

    def test_print_payload(self):
        self.client.credentials(**auth_header(self.sales))
        created = self.client.post(self.list_url, self._payload(), format="json")
        qid = created.data["data"]["id"]
        printed = self.client.get(reverse("quotations-print", args=[qid]))
        self.assertEqual(printed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(printed.data["data"]["items"]), 1)
