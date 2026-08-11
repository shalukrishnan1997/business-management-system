from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.expenses.models import ExpenseCategoryStatus, ExpenseStatus

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


class ExpenseAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="exp-admin@example.com",
            password="StrongPass123!",
            first_name="Exp",
            last_name="Admin",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_staff=True,
        )
        self.accountant = User.objects.create_user(
            email="exp-acct@example.com",
            password="StrongPass123!",
            first_name="Exp",
            last_name="Acct",
            role=UserRole.ACCOUNTANT,
            status=UserStatus.ACTIVE,
        )
        self.sales = User.objects.create_user(
            email="exp-sales@example.com",
            password="StrongPass123!",
            first_name="Exp",
            last_name="Sales",
            role=UserRole.SALES_STAFF,
            status=UserStatus.ACTIVE,
        )
        self.categories_url = reverse("expense-categories-list")
        self.expenses_url = reverse("expenses-list")

    def test_category_and_expense_flow(self):
        self.client.credentials(**auth_header(self.accountant))

        cat = self.client.post(
            self.categories_url,
            {"name": "Office Supplies", "description": "Stationery"},
            format="json",
        )
        self.assertEqual(cat.status_code, status.HTTP_201_CREATED, cat.data)
        cat_id = cat.data["data"]["id"]

        created = self.client.post(
            self.expenses_url,
            {
                "category": cat_id,
                "title": "Printer paper",
                "amount": "45.50",
                "payment_method": "cash",
                "vendor_name": "Stationery Mart",
            },
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        self.assertEqual(created.data["data"]["expense_number"], "EXP-0001")
        self.assertEqual(created.data["data"]["amount"], "45.50")
        eid = created.data["data"]["id"]

        updated = self.client.patch(
            reverse("expenses-detail", args=[eid]),
            {"amount": "50.00", "title": "Printer paper (A4)"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK, updated.data)
        self.assertEqual(updated.data["data"]["amount"], "50.00")

        summary = self.client.get(reverse("expenses-summary"))
        self.assertEqual(summary.status_code, status.HTTP_200_OK)
        self.assertEqual(summary.data["data"]["total_amount"], "50.00")
        self.assertEqual(summary.data["data"]["count"], 1)

        cancelled = self.client.post(reverse("expenses-cancel", args=[eid]))
        self.assertEqual(cancelled.status_code, status.HTTP_200_OK)
        self.assertEqual(cancelled.data["data"]["status"], ExpenseStatus.CANCELLED)

        summary2 = self.client.get(reverse("expenses-summary"))
        self.assertEqual(summary2.data["data"]["total_amount"], "0.00")
        self.assertEqual(summary2.data["data"]["count"], 0)

    def test_sales_staff_cannot_write_expenses(self):
        self.client.credentials(**auth_header(self.admin))
        cat = self.client.post(
            self.categories_url, {"name": "Travel"}, format="json"
        )
        cat_id = cat.data["data"]["id"]

        self.client.credentials(**auth_header(self.sales))
        denied = self.client.post(
            self.expenses_url,
            {
                "category": cat_id,
                "title": "Taxi",
                "amount": "20.00",
            },
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_category_blocked_and_soft_deactivate(self):
        self.client.credentials(**auth_header(self.admin))
        cat = self.client.post(
            self.categories_url, {"name": "Utilities"}, format="json"
        )
        cat_id = cat.data["data"]["id"]

        self.client.post(
            self.expenses_url,
            {"category": cat_id, "title": "Electricity", "amount": "100.00"},
            format="json",
        )

        delete_blocked = self.client.delete(
            reverse("expense-categories-detail", args=[cat_id])
        )
        self.assertEqual(delete_blocked.status_code, status.HTTP_400_BAD_REQUEST)

        # Soft deactivate empty-style: update status via PATCH then block new expense
        from apps.expenses.models import ExpenseCategory

        ExpenseCategory.objects.filter(pk=cat_id).update(
            status=ExpenseCategoryStatus.INACTIVE
        )
        blocked = self.client.post(
            self.expenses_url,
            {"category": cat_id, "title": "Water", "amount": "30.00"},
            format="json",
        )
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)
