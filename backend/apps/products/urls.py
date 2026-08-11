from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductLookupView, ProductViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"products", ProductViewSet, basename="products")

urlpatterns = [
    path(
        "products/lookup/",
        ProductLookupView.as_view(),
        name="products-lookup",
    ),
    *router.urls,
]
