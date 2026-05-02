"""Admin/internal catalog views (Django REST). High-volume reads use FastAPI."""

from __future__ import annotations

from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsStaff

from .models import Brand, Category, Product, ProductVariant
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    ProductSerializer,
    ProductVariantSerializer,
    ProductWriteSerializer,
)


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by("name")
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated, IsStaff]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "slug"]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("sort_order", "name")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsStaff]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "slug"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = (
        Product.objects.all()
        .select_related("brand")
        .prefetch_related("variants", "images", "categories")
        .order_by("-created_at")
    )
    permission_classes = [IsAuthenticated, IsStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug", "variants__sku", "brand__name"]
    ordering_fields = ["name", "created_at", "rating_avg", "sold_count"]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return ProductWriteSerializer
        return ProductSerializer


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.select_related("product").order_by("product__name", "name")
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticated, IsStaff]
    filter_backends = [filters.SearchFilter]
    search_fields = ["sku", "barcode", "product__name"]
