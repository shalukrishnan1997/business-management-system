"""
Production settings — stricter security defaults.
"""
from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = config("SECRET_KEY")  # noqa: F405  # required — no insecure default

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())  # noqa: F405

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME"),  # noqa: F405
        "USER": config("DB_USER"),  # noqa: F405
        "PASSWORD": config("DB_PASSWORD"),  # noqa: F405
        "HOST": config("DB_HOST", default="127.0.0.1"),  # noqa: F405
        "PORT": config("DB_PORT", default="3306"),  # noqa: F405
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

CELERY_TASK_ALWAYS_EAGER = False
