from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.views import APIView

from apps.common.permissions import (
    CanAccessDashboard,
    CanAccessReports,
    IsAuthenticatedAndActive,
)
from apps.common.responses import success_response

from .exporters import EXPORTERS
from .serializers import (
    DashboardChartsQuerySerializer,
    DateRangeQuerySerializer,
    ExportQuerySerializer,
    RecentActivityQuerySerializer,
)
from .services import (
    REPORT_BUILDERS,
    get_dashboard_charts,
    get_dashboard_kpis,
    get_recent_activity,
)


class DashboardSummaryView(APIView):
    module = "dashboard"
    permission_classes = [IsAuthenticatedAndActive, CanAccessDashboard]

    @extend_schema(tags=["Dashboard"])
    def get(self, request):
        return success_response(
            data=get_dashboard_kpis(),
            message="Dashboard KPIs.",
        )


class DashboardChartsView(APIView):
    module = "dashboard"
    permission_classes = [IsAuthenticatedAndActive, CanAccessDashboard]

    @extend_schema(tags=["Dashboard"])
    def get(self, request):
        query = DashboardChartsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return success_response(
            data=get_dashboard_charts(days=query.validated_data.get("days", 30)),
            message="Dashboard charts.",
        )


class DashboardRecentView(APIView):
    module = "dashboard"
    permission_classes = [IsAuthenticatedAndActive, CanAccessDashboard]

    @extend_schema(tags=["Dashboard"])
    def get(self, request):
        query = RecentActivityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return success_response(
            data=get_recent_activity(limit=query.validated_data.get("limit", 15)),
            message="Recent activity.",
        )


class ReportListView(APIView):
    module = "reports"
    permission_classes = [IsAuthenticatedAndActive, CanAccessReports]

    @extend_schema(tags=["Reports"])
    def get(self, request):
        return success_response(
            data={
                "reports": sorted(REPORT_BUILDERS.keys()),
                "export_formats": ["csv", "xlsx", "pdf"],
            },
            message="Available reports.",
        )


class ReportDetailView(APIView):
    module = "reports"
    permission_classes = [IsAuthenticatedAndActive, CanAccessReports]

    def _build(self, report_type: str, query_data: dict) -> dict:
        builder = REPORT_BUILDERS.get(report_type)
        if not builder:
            raise NotFound(detail=f"Unknown report: {report_type}")
        if report_type == "inventory":
            return builder()
        return builder(
            date_from=query_data.get("date_from"),
            date_to=query_data.get("date_to"),
        )

    @extend_schema(tags=["Reports"])
    def get(self, request, report_type: str):
        query = DateRangeQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = self._build(report_type, query.validated_data)
        return success_response(data=data, message=f"{report_type} report.")


class ReportExportView(APIView):
    module = "reports"
    permission_classes = [IsAuthenticatedAndActive, CanAccessReports]

    @extend_schema(tags=["Reports"])
    def get(self, request, report_type: str):
        query = ExportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        builder = REPORT_BUILDERS.get(report_type)
        if not builder:
            raise NotFound(detail=f"Unknown report: {report_type}")

        fmt = query.validated_data.get("export_format", "csv")
        exporter = EXPORTERS.get(fmt)
        if not exporter:
            raise ValidationError({"export_format": ["Unsupported export format."]})

        if report_type == "inventory":
            report = builder()
        else:
            report = builder(
                date_from=query.validated_data.get("date_from"),
                date_to=query.validated_data.get("date_to"),
            )
        return exporter(report)
