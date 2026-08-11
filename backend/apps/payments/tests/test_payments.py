from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.customers.models import Customer
from apps.customers.services import get_outstanding_balance
from apps.invoices.models import InvoiceStatus
from apps.invoices.services import create_invoice, send_invoice
from apps.products.models import Category
from apps.products.services import create_product
from apps.purchases.models import PurchaseStatus
from apps.purchases.services import create_purchase, receive_purchase
from apps.suppliers.models import Supplier
from apps.suppliers.services import get_outstanding_balance as get_supplier_outstanding

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class PaymentAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="pay-admin@example.com",
            password="StrongPass123!",
            first_name="Pay",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.accountant = User.objects.create_user(
            email="pay-acct@example.com",
            password="StrongPass123!",
            first_name="Pay",
            last_name="Acct",
            role=UserRole.ACCOUNTANT,
            status=UserStatus.ACTIVE,
        )
        self.category = Category.objects.create(name="Pay Cat")
        self.customer = Customer.objects.create(
            customer_code="CUS-9201",
            name="Payment Customer",
            email="pay@customer.test",
            opening_balance=Decimal("0.00"),
            created_by=self.admin,
        )
        self.supplier = Supplier.objects.create(
            supplier_code="SUP-9201",
            name="Payment Supplier",
            opening_balance=Decimal("0.00"),
            created_by=self.admin,
        )
        self.product = create_product(
            data={
                "name": "Payable Item",
                "category": self.category,
                "purchase_price": Decimal("40.00"),
                "selling_price": Decimal("80.00"),
            },
            user=self.admin,
            opening_stock=Decimal("0.000"),
        )
        self.list_url = reverse("payments-list")
        self.invoice = create_invoice(
            data={
                "customer": self.customer,
                "discount": Decimal("0.00"),
                "tax": Decimal("0.00"),
                "notes": "",
            },
            items_data=[
                {
                    "product": self.product,
                    "quantity": Decimal("5.000"),
                    "unit_price": Decimal("80.00"),
                    "discount": Decimal("0.00"),
                    "tax": Decimal("0.00"),
                }
            ],
            user=self.admin,
        )
        send_invoice(self.invoice)

    def test_partial_and_full_invoice_payment(self):
        self.client.credentials(**auth_header(self.accountant))
        self.assertEqual(get_outstanding_balance(self.customer), Decimal("400.00"))

        partial = self.client.post(
            self.list_url,
            {
                "payment_type": "customer_receipt",
                "customer": self.customer.id,
                "reference_type": "invoice",
                "reference_id": self.invoice.id,
                "amount": "150.00",
                "payment_method": "upi",
            },
            format="json",
        )
        self.assertEqual(partial.status_code, status.HTTP_201_CREATED, partial.data)
        self.assertEqual(partial.data["data"]["payment_number"], "PAY-0001")
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.paid_amount, Decimal("150.00"))
        self.assertEqual(self.invoice.balance, Decimal("250.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.PARTIALLY_PAID)
        self.assertEqual(get_outstanding_balance(self.customer), Decimal("250.00"))

        full = self.client.post(
            self.list_url,
            {
                "payment_type": "customer_receipt",
                "customer": self.customer.id,
                "reference_type": "invoice",
                "reference_id": self.invoice.id,
                "amount": "250.00",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(full.status_code, status.HTTP_201_CREATED, full.data)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.balance, Decimal("0.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.PAID)
        self.assertEqual(get_outstanding_balance(self.customer), Decimal("0.00"))

        history = self.client.get(
            reverse("customers-payment-history", args=[self.customer.id])
        )
        self.assertEqual(history.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history.data["data"]["results"]), 2)

        receipt = self.client.get(
            reverse("payments-receipt", args=[partial.data["data"]["id"]])
        )
        self.assertEqual(receipt.status_code, status.HTTP_200_OK)
        self.assertEqual(receipt.data["data"]["payment_number"], "PAY-0001")

    def test_supplier_payment_against_purchase(self):
        self.client.credentials(**auth_header(self.admin))
        purchase = create_purchase(
            data={
                "supplier": self.supplier,
                "paid_amount": Decimal("0.00"),
                "shipping_charge": Decimal("0.00"),
                "notes": "",
            },
            items_data=[
                {
                    "product": self.product,
                    "quantity": Decimal("10.000"),
                    "unit_price": Decimal("40.00"),
                    "tax": Decimal("0.00"),
                    "discount": Decimal("0.00"),
                }
            ],
            user=self.admin,
        )
        receive_purchase(purchase=purchase, user=self.admin)
        purchase.refresh_from_db()
        self.assertEqual(purchase.purchase_status, PurchaseStatus.RECEIVED)
        self.assertEqual(get_supplier_outstanding(self.supplier), Decimal("400.00"))

        paid = self.client.post(
            self.list_url,
            {
                "payment_type": "supplier_payment",
                "supplier": self.supplier.id,
                "reference_type": "purchase",
                "reference_id": purchase.id,
                "amount": "100.00",
                "payment_method": "bank_transfer",
            },
            format="json",
        )
        self.assertEqual(paid.status_code, status.HTTP_201_CREATED, paid.data)
        purchase.refresh_from_db()
        self.assertEqual(purchase.paid_amount, Decimal("100.00"))
        self.assertEqual(purchase.due_amount, Decimal("300.00"))
        self.assertEqual(get_supplier_outstanding(self.supplier), Decimal("300.00"))

        hist = self.client.get(
            reverse("suppliers-payment-history", args=[self.supplier.id])
        )
        self.assertEqual(hist.status_code, status.HTTP_200_OK)
        self.assertEqual(len(hist.data["data"]["results"]), 1)

    def test_manual_receipt_reduces_outstanding(self):
        self.client.credentials(**auth_header(self.accountant))
        before = get_outstanding_balance(self.customer)
        self.assertEqual(before, Decimal("400.00"))

        manual = self.client.post(
            self.list_url,
            {
                "payment_type": "customer_receipt",
                "customer": self.customer.id,
                "reference_type": "manual",
                "amount": "50.00",
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(manual.status_code, status.HTTP_201_CREATED, manual.data)
        # Invoice balance unchanged; unallocated receipt reduces AR
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.balance, Decimal("400.00"))
        self.assertEqual(get_outstanding_balance(self.customer), Decimal("350.00"))
