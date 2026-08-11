"""
Celery tasks for notifications and scheduled checks.

Runs eagerly when CELERY_TASK_ALWAYS_EAGER=True (default locally / tests).
"""
from celery import shared_task


@shared_task(name="apps.notifications.tasks.create_notification_task")
def create_notification_task(
    user_id: int,
    title: str,
    message: str = "",
    notification_type: str = "info",
    link: str = "",
    module: str = "",
    object_id: str = "",
) -> int:
    from django.contrib.auth import get_user_model

    from .services import create_notification

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return 0
    note = create_notification(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        module=module,
        object_id=object_id,
    )
    return note.id


@shared_task(name="apps.notifications.tasks.notify_roles_task")
def notify_roles_task(
    roles: list,
    title: str,
    message: str = "",
    notification_type: str = "info",
    link: str = "",
    module: str = "",
    object_id: str = "",
) -> int:
    from .services import notify_roles

    return notify_roles(
        roles=roles,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        module=module,
        object_id=object_id,
    )


@shared_task(name="apps.notifications.tasks.mark_overdue_invoices_and_notify")
def mark_overdue_invoices_and_notify() -> dict:
    from apps.accounts.models import UserRole
    from apps.invoices.models import Invoice, InvoiceStatus
    from apps.invoices.services import mark_overdue_invoices

    from .models import NotificationType
    from .services import notify_roles

    updated = mark_overdue_invoices()
    overdue_count = Invoice.objects.filter(status=InvoiceStatus.OVERDUE).count()
    if updated or overdue_count:
        notify_roles(
            roles={UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.SUPER_ADMIN},
            title="Overdue invoices check",
            message=(
                f"Marked {updated} invoice(s) overdue. "
                f"Currently {overdue_count} overdue."
            ),
            notification_type=NotificationType.WARNING,
            link="/invoices?status=overdue",
            module="invoices",
        )
    return {"updated": updated, "overdue_count": overdue_count}


@shared_task(name="apps.notifications.tasks.check_low_stock_and_notify")
def check_low_stock_and_notify() -> dict:
    from apps.accounts.models import UserRole
    from apps.products.services import low_stock_queryset

    from .models import NotificationType
    from .services import notify_roles

    qs = low_stock_queryset().order_by("name")[:20]
    count = low_stock_queryset().count()
    if count == 0:
        return {"count": 0}
    sample = ", ".join(f"{p.product_code}" for p in qs)
    more = f" (+{count - qs.count()} more)" if count > qs.count() else ""
    notify_roles(
        roles={
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.INVENTORY_STAFF,
            UserRole.SUPER_ADMIN,
        },
        title="Low stock alert",
        message=f"{count} product(s) at or below reorder level: {sample}{more}",
        notification_type=NotificationType.WARNING,
        link="/products?low_stock=true",
        module="products",
    )
    return {"count": count}
