from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.audit.models import AuditLog
from apps.invoices.models import InvoiceStatus
from apps.invoices.services import create_invoice, send_invoice
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.products.models import Category
from apps.products.services import create_product

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class NotificationAuditAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="aud-admin@example.com",
            password="StrongPass123!",
            first_name="Aud",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.viewer = User.objects.create_user(
            email="aud-viewer@example.com",
            password="StrongPass123!",
            first_name="Aud",
            last_name="Viewer",
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE,
        )
        self.category = Category.objects.create(name="Audit Cat")
        self.product = create_product(
            data={
                "name": "Audit Product",
                "category": self.category,
                "selling_price": Decimal("25.00"),
                "minimum_stock": Decimal("10.000"),
                "reorder_level": Decimal("10.000"),
            },
            user=self.admin,
            opening_stock=Decimal("2.000"),
        )

    def test_notifications_list_mark_read_and_unread_count(self):
        create_notification(
            user=self.viewer,
            title="Hello",
            message="World",
            link="/dashboard",
        )
        create_notification(user=self.admin, title="Admin only")

        self.client.credentials(**auth_header(self.viewer))
        listed = self.client.get(reverse("notifications-list"))
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(listed.data["count"], 1)

        unread = self.client.get(reverse("notifications-unread-count"))
        self.assertEqual(unread.status_code, status.HTTP_200_OK)
        self.assertEqual(unread.data["data"]["unread_count"], 1)

        marked = self.client.post(reverse("notifications-mark-all-read"))
        self.assertEqual(marked.status_code, status.HTTP_200_OK)
        self.assertEqual(marked.data["data"]["unread_count"], 0)
        self.assertTrue(Notification.objects.get(user=self.viewer).is_read)

    def test_low_stock_job_notifies_admin(self):
        self.client.credentials(**auth_header(self.admin))
        before = Notification.objects.filter(user=self.admin).count()
        resp = self.client.post(reverse("notifications-job-low-stock"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertGreaterEqual(resp.data["data"]["count"], 1)
        self.assertGreater(
            Notification.objects.filter(user=self.admin, module="products").count(),
            before,
        )

    def test_overdue_job(self):
        from apps.customers.models import Customer

        customer = Customer.objects.create(
            customer_code="CUS-1701",
            name="Audit Customer",
            created_by=self.admin,
        )
        invoice = create_invoice(
            data={
                "customer": customer,
                "due_date": timezone.localdate() - timedelta(days=2),
            },
            items_data=[
                {
                    "product": self.product,
                    "quantity": Decimal("1.000"),
                    "unit_price": Decimal("25.00"),
                }
            ],
            user=self.admin,
        )
        send_invoice(invoice)

        self.client.credentials(**auth_header(self.admin))
        resp = self.client.post(reverse("notifications-job-overdue"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, InvoiceStatus.OVERDUE)

    def test_audit_middleware_and_admin_list(self):
        self.client.credentials(**auth_header(self.admin))
        # Mutating call should create an audit row
        self.client.post(
            reverse("expense-categories-list"),
            {"name": "Audit Expense Cat"},
            format="json",
        )
        self.assertTrue(
            AuditLog.objects.filter(module="expenses", method="POST").exists()
        )
        log = AuditLog.objects.filter(module="expenses", method="POST").latest("id")
        self.assertEqual(log.user_id, self.admin.id)

        listed = self.client.get(reverse("audit-logs-list"))
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(listed.data["count"], 1)

        self.client.credentials(**auth_header(self.viewer))
        denied = self.client.get(reverse("audit-logs-list"))
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
