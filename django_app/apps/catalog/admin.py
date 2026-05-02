from __future__ import annotations

from django.contrib import admin

from .models import (
    Attribute,
    AttributeOption,
    Brand,
    Category,
    Product,
    ProductImage,
    ProductVariant,
)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("sku", "name", "price", "compare_at_price", "is_default", "is_active")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "alt_text", "sort_order", "is_primary")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "sort_order", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "kind", "is_filterable")
    list_filter = ("kind", "is_filterable")
    search_fields = ("code", "name")


@admin.register(AttributeOption)
class AttributeOptionAdmin(admin.ModelAdmin):
    list_display = ("attribute", "value", "label", "sort_order")
    list_filter = ("attribute",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "status", "is_featured", "rating_avg", "sold_count")
    list_filter = ("status", "is_featured", "brand")
    search_fields = ("name", "slug", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline, ProductImageInline]
    autocomplete_fields = ("brand", "categories")


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("sku", "barcode", "product__name")
