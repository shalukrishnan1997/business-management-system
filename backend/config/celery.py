"""
Celery application for background tasks.

Early phases run tasks eagerly (synchronously) so Redis is optional.
Enable a real broker in Phase 17 via CELERY_TASK_ALWAYS_EAGER=False and REDIS_URL.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
