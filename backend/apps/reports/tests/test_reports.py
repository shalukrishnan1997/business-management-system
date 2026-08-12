from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.customers.models import Customer
from apps.expenses.models import ExpenseCategory
from apps.expenses.services import create_expense
from apps.products.models import Category
from apps.products.services import create_product
from apps.sales.services import create_sale

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class DashboardReportsAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="dash-admin@example.com",
            password="StrongPass123!",
            first_name="Dash",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.viewer = User.objects.create_user(
            email="dash-viewer@example.com",
            password="StrongPass123!",
            first_name="Dash",
            last_name="Viewer",
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE,
        )
        self.category = Category.objects.create(name="Dash Cat")
        self.customer = Customer.objects.create(
            customer_code="CUS-1601",
            name="Dashboard Customer",
            created_by=self.admin,
        )
        self.product = create_product(
            data={
                "name": "Dash Product",
                "category": self.category,
                "selling_price": Decimal("100.00"),
                "minimum_stock": Decimal("5.000"),
                "reorder_level": Decimal("5.000"),
            },
            user=self.admin,
            opening_stock=Decimal("2.000"),
        )
        create_sale(
            data={
                "customer": self.customer,
                "paid_amount": Decimal("0.00"),
                "shipping": Decimal("0.00"),
            },
            items_data=[
                {
                    "product": self.product,
                    "quantity": Decimal("1.000"),
                    "unit_price": Decimal("100.00"),
                    "tax": Decimal("0.00"),
                    "discount": Decimal("0.00"),
                }
            ],
            user=self.admin,
        )
        exp_cat = ExpenseCategory.objects.create(name="Ops")
        create_expense(
            data={
                "category": exp_cat,
                "title": "Internet",
                "amount": Decimal("999.00"),
            },
            user=self.admin,
        )

    def test_dashboard_endpoints(self):
        self.client.credentials(**auth_header(self.viewer))
        summary = self.client.get(reverse("dashboard-summary"))
        self.assertEqual(summary.status_code, status.HTTP_200_OK, summary.data)
        self.assertIn("counts", summary.data["data"])
        self.assertIn("money", summary.data["data"])
        self.assertGreaterEqual(summary.data["data"]["counts"]["low_stock"], 1)
        self.assertEqual(summary.data["data"]["money"]["sales_today"], "100.00")

        charts = self.client.get(reverse("dashboard-charts"), {"days": 7})
        self.assertEqual(charts.status_code, status.HTTP_200_OK)
        self.assertEqual(len(charts.data["data"]["sales_vs_purchases"]), 7)

        recent = self.client.get(reverse("dashboard-recent"), {"limit": 5})
        self.assertEqual(recent.status_code, status.HTTP_200_OK)
        self.assertTrue(len(recent.data["data"]["results"]) >= 1)

    def test_reports_and_exports(self):
        self.client.credentials(**auth_header(self.admin))
        listed = self.client.get(reverse("reports-list"))
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertIn("sales", listed.data["data"]["reports"])

        sales = self.client.get(reverse("reports-detail", args=["sales"]))
        self.assertEqual(sales.status_code, status.HTTP_200_OK)
        self.assertEqual(sales.data["data"]["summary"]["count"], 1)
        self.assertEqual(sales.data["data"]["summary"]["grand_total"], "100.00")

        expenses = self.client.get(reverse("reports-detail", args=["expenses"]))
        self.assertEqual(expenses.status_code, status.HTTP_200_OK)
        self.assertEqual(expenses.data["data"]["summary"]["total_amount"], "999.00")

        inventory = self.client.get(reverse("reports-detail", args=["inventory"]))
        self.assertEqual(inventory.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(inventory.data["data"]["summary"]["low_stock_count"], 1)

        csv_resp = self.client.get(
            reverse("reports-export", args=["sales"]), {"export_format": "csv"}
        )
        self.assertEqual(csv_resp.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", csv_resp["Content-Type"])
        self.assertIn(b"SAL-", csv_resp.content)

        xlsx_resp = self.client.get(
            reverse("reports-export", args=["expenses"]), {"export_format": "xlsx"}
        )
        self.assertEqual(xlsx_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(
            xlsx_resp["Content-Type"].startswith(
                "application/vnd.openxmlformats-officedocument"
            )
        )

        pdf_resp = self.client.get(
            reverse("reports-export", args=["inventory"]), {"export_format": "pdf"}
        )
        self.assertEqual(pdf_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(pdf_resp.content.startswith(b"%PDF"))

        missing = self.client.get(reverse("reports-detail", args=["unknown"]))
        self.assertEqual(missing.status_code, status.HTTP_404_NOT_FOUND)

    def test_all_report_types_and_export_formats(self):
        self.client.credentials(**auth_header(self.admin))
        types = self.client.get(reverse("reports-list")).data["data"]["reports"]
        self.assertEqual(
            set(types),
            {"sales", "purchases", "invoices", "payments", "expenses", "inventory"},
        )

        for report_type in types:
            detail = self.client.get(reverse("reports-detail", args=[report_type]))
            self.assertEqual(
                detail.status_code, status.HTTP_200_OK, f"{report_type}: {detail.data}"
            )
            self.assertIn("summary", detail.data["data"])
            self.assertIn("rows", detail.data["data"])
            self.assertIn("columns", detail.data["data"])

            for fmt in ("csv", "xlsx", "pdf"):
                exported = self.client.get(
                    reverse("reports-export", args=[report_type]),
                    {"export_format": fmt},
                )
                self.assertEqual(
                    exported.status_code,
                    status.HTTP_200_OK,
                    f"{report_type}/{fmt}",
                )
                self.assertTrue(len(exported.content) > 0)
