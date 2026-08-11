from rest_framework.routers import DefaultRouter

from .views import QuotationViewSet

router = DefaultRouter()
router.register(r"quotations", QuotationViewSet, basename="quotations")

urlpatterns = router.urls
