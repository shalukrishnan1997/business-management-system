from rest_framework.routers import DefaultRouter

from .views import SalesOrderViewSet

router = DefaultRouter()
router.register(r"sales", SalesOrderViewSet, basename="sales")

urlpatterns = router.urls
