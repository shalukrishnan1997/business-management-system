"""
Notification helpers — prefer these over Django signals.
"""
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserStatus

from .models import Notification, NotificationType

User = get_user_model()


def create_notification(
    *,
    user,
    title: str,
    message: str = "",
    notification_type: str = NotificationType.INFO,
    link: str = "",
    module: str = "",
    object_id: str = "",
) -> Notification:
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        module=module,
        object_id=str(object_id) if object_id not in (None, "") else "",
    )


def notify_users(
    *,
    users,
    title: str,
    message: str = "",
    notification_type: str = NotificationType.INFO,
    link: str = "",
    module: str = "",
    object_id: str = "",
) -> int:
    created = 0
    for user in users:
        create_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
            module=module,
            object_id=object_id,
        )
        created += 1
    return created


def notify_roles(
    *,
    roles: list | set,
    title: str,
    message: str = "",
    notification_type: str = NotificationType.INFO,
    link: str = "",
    module: str = "",
    object_id: str = "",
) -> int:
    users = User.objects.filter(
        role__in=list(roles),
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    return notify_users(
        users=users,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        module=module,
        object_id=object_id,
    )


def unread_count(user) -> int:
    return Notification.objects.filter(user=user, is_read=False).count()


@transaction.atomic
def mark_notifications_read(*, user, ids: list[int] | None = None) -> int:
    qs = Notification.objects.filter(user=user, is_read=False)
    if ids is not None:
        qs = qs.filter(id__in=ids)
    now = timezone.now()
    return qs.update(is_read=True, read_at=now)


def delete_notification(*, user, notification: Notification) -> None:
    if notification.user_id != user.id:
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("You can only delete your own notifications.")
    notification.delete()
