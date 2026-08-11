from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.user_views import (
    CustomersPermissionDemoView,
    MyPermissionsView,
    UserViewSet,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
    path("rbac/me/", MyPermissionsView.as_view(), name="rbac-me"),
    path(
        "rbac/demo/customers/",
        CustomersPermissionDemoView.as_view(),
        name="rbac-demo-customers",
    ),
]
