from __future__ import annotations

from rest_framework import serializers

from .models import (
    Attribute,
    AttributeOption,
    Brand,
    Category,
    Product,
    ProductImage,
    ProductVariant,
)


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ("id", "name", "slug", "description", "logo", "is_active")


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "parent",
            "description",
            "image",
            "sort_order",
            "is_active",
            "children",
        )

    def get_children(self, obj):
        if not getattr(obj, "_include_children", False):
            return []
        return CategorySerializer(obj.children.filter(is_active=True), many=True).data


class AttributeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOption
        fields = ("id", "value", "label", "sort_order")


class AttributeSerializer(serializers.ModelSerializer):
    options = AttributeOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = ("id", "code", "name", "kind", "is_filterable", "is_required", "options")


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "alt_text", "sort_order", "is_primary", "variant")


class ProductVariantSerializer(serializers.ModelSerializer):
    discount_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "barcode",
            "name",
            "price",
            "compare_at_price",
            "currency",
            "weight_g",
            "is_default",
            "is_active",
            "attributes_snapshot",
            "discount_percent",
        )


class ProductSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "short_description",
            "description",
            "brand",
            "categories",
            "status",
            "is_featured",
            "rating_avg",
            "rating_count",
            "sold_count",
            "metadata",
            "variants",
            "images",
            "created_at",
            "updated_at",
        )


class ProductWriteSerializer(serializers.ModelSerializer):
    """Slimmer serializer for create/update from admin."""

    class Meta:
        model = Product
        fields = (
            "name",
            "slug",
            "short_description",
            "description",
            "brand",
            "categories",
            "attributes",
            "status",
            "is_featured",
            "seo_title",
            "seo_description",
            "seo_keywords",
            "metadata",
        )
