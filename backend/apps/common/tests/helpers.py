"""Shared helpers for API tests (Phase 23)."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserRole, UserStatus
from apps.customers.models import Customer
from apps.products.models import Category
from apps.products.services import create_product
from apps.suppliers.models import Supplier

User = get_user_model()


def auth_header(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}


def make_user(
    *,
    email: str,
    role: str = UserRole.ADMIN,
    password: str = "StrongPass123!",
    is_staff: bool = False,
    **extra,
):
    return User.objects.create_user(
        email=email,
        password=password,
        first_name=extra.pop("first_name", "Test"),
        last_name=extra.pop("last_name", "User"),
        role=role,
        status=UserStatus.ACTIVE,
        is_staff=is_staff,
        **extra,
    )


def seed_party_catalog(*, user, prefix: str = "WF"):
    """Minimal customer, supplier, category, and product for workflow tests."""
    category = Category.objects.create(name=f"{prefix} Cat")
    customer = Customer.objects.create(
        customer_code=f"CUS-{prefix}",
        name=f"{prefix} Customer",
        opening_balance=Decimal("0.00"),
        created_by=user,
    )
    supplier = Supplier.objects.create(
        supplier_code=f"SUP-{prefix}",
        name=f"{prefix} Supplier",
        opening_balance=Decimal("0.00"),
        created_by=user,
    )
    product = create_product(
        data={
            "name": f"{prefix} Product",
            "category": category,
            "purchase_price": Decimal("40.00"),
            "selling_price": Decimal("100.00"),
        },
        user=user,
        opening_stock=Decimal("0.000"),
    )
    return {
        "category": category,
        "customer": customer,
        "supplier": supplier,
        "product": product,
    }
