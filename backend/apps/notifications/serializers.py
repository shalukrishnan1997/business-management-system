from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "title",
            "message",
            "notification_type",
            "link",
            "is_read",
            "read_at",
            "module",
            "object_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class MarkReadSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
        help_text="Omit or empty to mark all unread as read.",
    )
