from django.urls import path

from .views import (
    DashboardChartsView,
    DashboardRecentView,
    DashboardSummaryView,
    ReportDetailView,
    ReportExportView,
    ReportListView,
)

urlpatterns = [
    path("dashboard/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("dashboard/charts/", DashboardChartsView.as_view(), name="dashboard-charts"),
    path("dashboard/recent/", DashboardRecentView.as_view(), name="dashboard-recent"),
    path("reports/", ReportListView.as_view(), name="reports-list"),
    # Export before detail so `/export/` is not swallowed by report_type routing.
    path(
        "reports/<str:report_type>/export/",
        ReportExportView.as_view(),
        name="reports-export",
    ),
    path(
        "reports/<str:report_type>/",
        ReportDetailView.as_view(),
        name="reports-detail",
    ),
]
