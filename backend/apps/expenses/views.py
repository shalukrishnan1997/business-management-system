from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import CanManageExpenses, IsAuthenticatedAndActive
from apps.common.responses import success_response

from .filters import ExpenseCategoryFilter, ExpenseFilter
from .models import Expense, ExpenseCategory
from .serializers import (
    ExpenseCategorySerializer,
    ExpenseCreateUpdateSerializer,
    ExpenseSerializer,
    ExpenseSummaryQuerySerializer,
)
from .services import (
    activate_category,
    cancel_expense,
    create_expense,
    deactivate_category,
    expense_summary,
    update_expense,
)


@extend_schema_view(
    list=extend_schema(tags=["Expense Categories"]),
    retrieve=extend_schema(tags=["Expense Categories"]),
    create=extend_schema(tags=["Expense Categories"]),
    update=extend_schema(tags=["Expense Categories"]),
    partial_update=extend_schema(tags=["Expense Categories"]),
    destroy=extend_schema(tags=["Expense Categories"]),
)
class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    module = "expenses"
    permission_classes = [IsAuthenticatedAndActive, CanManageExpenses]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ExpenseCategoryFilter
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]
    serializer_class = ExpenseCategorySerializer

    def get_queryset(self):
        return ExpenseCategory.objects.annotate(expenses_count=Count("expenses"))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(
            data=self.get_serializer(self.get_object()).data,
            message="Expense category retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        category = self.get_queryset().get(pk=category.pk)
        return success_response(
            data=self.get_serializer(category).data,
            message="Expense category created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        category = self.get_object()
        serializer = self.get_serializer(category, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        category = self.get_queryset().get(pk=category.pk)
        return success_response(
            data=self.get_serializer(category).data,
            message="Expense category updated.",
        )

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.expenses.exists():
            return Response(
                {
                    "success": False,
                    "message": (
                        "Cannot delete a category that has expenses. "
                        "Deactivate it instead."
                    ),
                    "errors": {"detail": ["Category has related expenses."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        deactivate_category(category)
        return success_response(message="Expense category deactivated.")

    @extend_schema(tags=["Expense Categories"])
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        category = activate_category(self.get_object())
        category = self.get_queryset().get(pk=category.pk)
        return success_response(
            data=self.get_serializer(category).data,
            message="Expense category activated.",
        )


@extend_schema_view(
    list=extend_schema(tags=["Expenses"]),
    retrieve=extend_schema(tags=["Expenses"]),
    create=extend_schema(tags=["Expenses"]),
    update=extend_schema(tags=["Expenses"]),
    partial_update=extend_schema(tags=["Expenses"]),
)
class ExpenseViewSet(viewsets.ModelViewSet):
    module = "expenses"
    permission_classes = [IsAuthenticatedAndActive, CanManageExpenses]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ExpenseFilter
    search_fields = [
        "expense_number",
        "title",
        "description",
        "vendor_name",
        "reference_number",
        "notes",
        "category__name",
    ]
    ordering_fields = ["expense_date", "amount", "created_at", "expense_number"]
    ordering = ["-expense_date", "-id"]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        return Expense.objects.select_related("category", "created_by")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ExpenseCreateUpdateSerializer
        return ExpenseSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = ExpenseSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(
            data=ExpenseSerializer(self.get_object(), context={"request": request}).data,
            message="Expense retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = create_expense(data=dict(serializer.validated_data), user=request.user)
        expense = self.get_queryset().get(pk=expense.pk)
        return success_response(
            data=ExpenseSerializer(expense, context={"request": request}).data,
            message="Expense recorded.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        expense = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        expense = update_expense(expense=expense, data=dict(serializer.validated_data))
        expense = self.get_queryset().get(pk=expense.pk)
        return success_response(
            data=ExpenseSerializer(expense, context={"request": request}).data,
            message="Expense updated.",
        )

    @extend_schema(tags=["Expenses"])
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        expense = cancel_expense(self.get_object())
        return success_response(
            data=ExpenseSerializer(expense, context={"request": request}).data,
            message="Expense cancelled.",
        )

    @extend_schema(tags=["Expenses"])
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        query = ExpenseSummaryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = expense_summary(
            date_from=query.validated_data.get("date_from"),
            date_to=query.validated_data.get("date_to"),
            category_id=query.validated_data.get("category"),
        )
        return success_response(data=data, message="Expense summary.")
