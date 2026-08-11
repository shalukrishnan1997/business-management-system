from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    InventoryLowStockView,
    StockAdjustInView,
    StockAdjustOutView,
    StockTransactionViewSet,
)

router = DefaultRouter()
router.register(
    r"inventory/transactions",
    StockTransactionViewSet,
    basename="stock-transactions",
)

urlpatterns = [
    path(
        "inventory/adjust-in/",
        StockAdjustInView.as_view(),
        name="inventory-adjust-in",
    ),
    path(
        "inventory/adjust-out/",
        StockAdjustOutView.as_view(),
        name="inventory-adjust-out",
    ),
    path(
        "inventory/low-stock/",
        InventoryLowStockView.as_view(),
        name="inventory-low-stock",
    ),
    *router.urls,
]
