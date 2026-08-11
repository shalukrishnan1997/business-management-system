from rest_framework.routers import DefaultRouter

from .views import ExpenseCategoryViewSet, ExpenseViewSet

router = DefaultRouter()
router.register(r"expense-categories", ExpenseCategoryViewSet, basename="expense-categories")
router.register(r"expenses", ExpenseViewSet, basename="expenses")

urlpatterns = router.urls
