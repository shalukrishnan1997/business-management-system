from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import CanManageProducts, IsAuthenticatedAndActive
from apps.common.responses import success_response

from .filters import CategoryFilter, ProductFilter
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductCreateUpdateSerializer,
    ProductPriceUpdateSerializer,
    ProductSerializer,
)
from .services import (
    activate_category,
    activate_product,
    create_product,
    deactivate_category,
    deactivate_product,
    get_inventory_history,
    low_stock_queryset,
    lookup_product,
    update_product_prices,
)


@extend_schema_view(
    list=extend_schema(tags=["Categories"]),
    retrieve=extend_schema(tags=["Categories"]),
    create=extend_schema(tags=["Categories"]),
    update=extend_schema(tags=["Categories"]),
    partial_update=extend_schema(tags=["Categories"]),
    destroy=extend_schema(tags=["Categories"]),
)
class CategoryViewSet(viewsets.ModelViewSet):
    module = "products"
    permission_classes = [IsAuthenticatedAndActive, CanManageProducts]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CategoryFilter
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.annotate(products_count=Count("products"))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(
            data=self.get_serializer(self.get_object()).data,
            message="Category retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        category = self.get_queryset().get(pk=category.pk)
        return success_response(
            data=self.get_serializer(category).data,
            message="Category created.",
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
            message="Category updated.",
        )

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.products.exists():
            return Response(
                {
                    "success": False,
                    "message": "Cannot delete a category that has products. Deactivate it instead.",
                    "errors": {"detail": ["Category has related products."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        deactivate_category(category)
        return success_response(message="Category deactivated.")

    @extend_schema(tags=["Categories"])
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        category = activate_category(self.get_object())
        category = self.get_queryset().get(pk=category.pk)
        return success_response(
            data=self.get_serializer(category).data,
            message="Category activated.",
        )


@extend_schema_view(
    list=extend_schema(tags=["Products"]),
    retrieve=extend_schema(tags=["Products"]),
    create=extend_schema(tags=["Products"]),
    update=extend_schema(tags=["Products"]),
    partial_update=extend_schema(tags=["Products"]),
    destroy=extend_schema(tags=["Products"]),
)
class ProductViewSet(viewsets.ModelViewSet):
    module = "products"
    permission_classes = [IsAuthenticatedAndActive, CanManageProducts]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["product_code", "barcode", "name", "description"]
    ordering_fields = [
        "name",
        "product_code",
        "selling_price",
        "purchase_price",
        "current_stock",
        "created_at",
    ]
    ordering = ["name"]

    def get_queryset(self):
        return Product.objects.select_related(
            "category", "supplier", "created_by"
        ).all()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = ProductSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        product = self.get_object()
        return success_response(
            data=ProductSerializer(product, context={"request": request}).data,
            message="Product retrieved.",
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        opening_stock = data.pop("opening_stock", None)
        product = create_product(
            data=data, user=request.user, opening_stock=opening_stock
        )
        return success_response(
            data=ProductSerializer(product, context={"request": request}).data,
            message="Product created.",
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        product = self.get_object()
        serializer = self.get_serializer(product, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.pop("opening_stock", None)  # ignored on update
        for attr, value in data.items():
            setattr(product, attr, value)
        product.save()
        return success_response(
            data=ProductSerializer(product, context={"request": request}).data,
            message="Product updated.",
        )

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        deactivate_product(product)
        return success_response(message="Product deactivated.")

    @extend_schema(tags=["Products"])
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        product = activate_product(self.get_object())
        return success_response(
            data=ProductSerializer(product, context={"request": request}).data,
            message="Product activated.",
        )

    @extend_schema(tags=["Products"])
    @action(detail=True, methods=["patch"], url_path="prices")
    def prices(self, request, pk=None):
        product = self.get_object()
        serializer = ProductPriceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = update_product_prices(product, **serializer.validated_data)
        return success_response(
            data=ProductSerializer(product, context={"request": request}).data,
            message="Product prices updated.",
        )

    @extend_schema(tags=["Products"])
    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        queryset = self.filter_queryset(low_stock_queryset())
        page = self.paginate_queryset(queryset)
        serializer = ProductSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @extend_schema(tags=["Products"])
    @action(detail=True, methods=["get"], url_path="inventory-history")
    def inventory_history(self, request, pk=None):
        product = self.get_object()
        return success_response(
            data={
                "product_id": product.id,
                "product_code": product.product_code,
                "current_stock": str(product.current_stock),
                "results": get_inventory_history(product),
                "meta": {
                    "linked": True,
                    "note": "Stock movements from inventory ledger.",
                },
            },
            message="Product inventory history.",
        )


@extend_schema(
    tags=["Products"],
    parameters=[
        OpenApiParameter(name="sku", required=False, type=str),
        OpenApiParameter(name="barcode", required=False, type=str),
    ],
)
class ProductLookupView(APIView):
    """Lookup a product by SKU (product_code) or barcode."""

    permission_classes = [IsAuthenticatedAndActive, CanManageProducts]

    def get(self, request):
        sku = request.query_params.get("sku")
        barcode = request.query_params.get("barcode")
        if not sku and not barcode:
            return Response(
                {
                    "success": False,
                    "message": "Provide sku or barcode query parameter.",
                    "errors": {"detail": ["sku or barcode is required."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        product = lookup_product(sku=sku, barcode=barcode)
        if not product:
            return Response(
                {
                    "success": False,
                    "message": "Product not found.",
                    "errors": {"detail": ["No matching product."]},
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return success_response(
            data=ProductSerializer(product, context={"request": request}).data,
            message="Product found.",
        )
