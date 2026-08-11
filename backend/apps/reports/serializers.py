from rest_framework import serializers


class DateRangeQuerySerializer(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)


class DashboardChartsQuerySerializer(serializers.Serializer):
    days = serializers.IntegerField(required=False, default=30, min_value=1, max_value=365)


class RecentActivityQuerySerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, default=15, min_value=1, max_value=50)


class ExportQuerySerializer(DateRangeQuerySerializer):
    export_format = serializers.ChoiceField(
        choices=["csv", "xlsx", "excel", "pdf"],
        required=False,
        default="csv",
    )
