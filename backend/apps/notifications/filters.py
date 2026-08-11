import django_filters

from .models import Notification, NotificationType


class NotificationFilter(django_filters.FilterSet):
    is_read = django_filters.BooleanFilter()
    notification_type = django_filters.ChoiceFilter(choices=NotificationType.choices)
    module = django_filters.CharFilter(field_name="module")

    class Meta:
        model = Notification
        fields = ["is_read", "notification_type", "module"]
