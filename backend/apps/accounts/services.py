"""
Auth-related side effects that should stay out of views.
"""
from django.conf import settings
from django.core.mail import send_mail

from .serializers import build_password_reset_payload


def send_password_reset_email(user, request=None):
    """
    Send password reset instructions.

    In development (console email backend), uid/token are also returned by the
    API for easier testing without reading the console.
    """
    payload = build_password_reset_payload(user)
    frontend_base = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    reset_link = (
        f"{frontend_base}/reset-password"
        f"?uid={payload['uid']}&token={payload['token']}"
    )

    subject = "Reset your Business Management System password"
    message = (
        f"Hello {user.full_name},\n\n"
        f"We received a request to reset your password.\n"
        f"Use the link below (or the uid/token in development):\n\n"
        f"{reset_link}\n\n"
        f"If you did not request this, you can ignore this email.\n"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    return payload
