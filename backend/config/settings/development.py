"""
Development settings — local machine defaults.
"""
from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# Phase 2 uses SQLite from base. Phase 3 will override with MySQL when USE_MYSQL=True.
USE_MYSQL = config("USE_MYSQL", default=False, cast=bool)  # noqa: F405

if USE_MYSQL:
    DATABASES = {  # noqa: F405
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

CORS_ALLOW_ALL_ORIGINS = False

# Helpful for local debugging of SQL (keep off unless needed)
# LOGGING = {...}
