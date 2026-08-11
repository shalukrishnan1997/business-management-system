"""
URL configuration for Business Management System.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.common.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health / smoke test for Phase 2
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),
    # OpenAPI schema & docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.accounts.rbac_urls")),
    path("api/v1/", include("apps.customers.urls")),
    path("api/v1/", include("apps.suppliers.urls")),
    path("api/v1/", include("apps.products.urls")),
    path("api/v1/", include("apps.inventory.urls")),
    path("api/v1/", include("apps.purchases.urls")),
    path("api/v1/", include("apps.sales.urls")),
    path("api/v1/", include("apps.quotations.urls")),
    path("api/v1/", include("apps.invoices.urls")),
    path("api/v1/", include("apps.payments.urls")),
    path("api/v1/", include("apps.expenses.urls")),
    path("api/v1/", include("apps.employees.urls")),
    path("api/v1/", include("apps.reports.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.audit.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
