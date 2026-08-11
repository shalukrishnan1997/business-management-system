"""
Create / update the local demo super admin.

Usage:
  python manage.py create_demo_admin
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import UserRole, UserStatus


class Command(BaseCommand):
    help = "Create a demo Super Admin user for local development."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="admin@bms.local")
        parser.add_argument("--password", default="Admin@12345")

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"].lower().strip()
        password = options["password"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": "Super",
                "last_name": "Admin",
                "role": UserRole.SUPER_ADMIN,
                "status": UserStatus.ACTIVE,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        user.first_name = "Super"
        user.last_name = "Admin"
        user.role = UserRole.SUPER_ADMIN
        user.status = UserStatus.ACTIVE
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f"{action} demo admin: {email} / {password}")
        )
