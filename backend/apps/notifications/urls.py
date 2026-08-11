from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet, RunLowStockCheckView, RunOverdueCheckView

router = DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notifications")

urlpatterns = [
    path(
        "notifications/jobs/low-stock/",
        RunLowStockCheckView.as_view(),
        name="notifications-job-low-stock",
    ),
    path(
        "notifications/jobs/overdue-invoices/",
        RunOverdueCheckView.as_view(),
        name="notifications-job-overdue",
    ),
    *router.urls,
]
