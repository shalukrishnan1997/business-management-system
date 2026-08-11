from rest_framework.routers import DefaultRouter

from .views import DepartmentViewSet, DesignationViewSet, EmployeeViewSet

router = DefaultRouter()
router.register(r"departments", DepartmentViewSet, basename="departments")
router.register(r"designations", DesignationViewSet, basename="designations")
router.register(r"employees", EmployeeViewSet, basename="employees")

urlpatterns = router.urls
