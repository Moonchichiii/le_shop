from django.contrib import admin
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin  # type: ignore
from unfold.decorators import display  # type: ignore

from .models import Category, Product


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = ("name", "price", "stock", "is_active", "is_featured", "is_new")
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ["name", "product_count"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductInline]

    @display(description="Products")
    def product_count(self, obj: Category) -> int:
        return obj.products.count()  # type: ignore


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = [
        "image_preview",
        "name",
        "category",
        "price",
        "stock",
        "is_active",
        "status_badge",
        "is_featured",
        "is_new",
        "created_at",
    ]
    list_editable = ["price", "stock", "is_active", "is_featured", "is_new"]
    list_filter = ["category", "is_active", "is_featured", "is_new", "created_at"]
    search_fields = ["name", "description", "category__name"]
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 25
    ordering = ["category__name", "-created_at"]

    @display(description="Photo")
    def image_preview(self, obj: Product) -> str:
        if not obj.image:
            return "-"
        style = "width: 50px; height: 50px; object-fit: cover;"
        html = (
            f'<img src="{obj.image.url}" class="rounded-lg border border-gray-200" '
            f'style="{style}" />'
        )
        return mark_safe(html)

    @display(description="Availability", label=True)
    def status_badge(self, obj: Product):
        if obj.stock > 0 and obj.is_active:
            return "In Stock", "success"
        if obj.is_active and obj.stock == 0:
            return "Sold Out", "warning"
        return "Inactive", "danger"

    fieldsets = (
        ("Basic Info", {"fields": (("name", "slug"), "category", "description")}),
        (
            "Pricing & Inventory",
            {
                "fields": (("price", "stock"), "is_active"),
                "classes": ("tab-panel",),
            },
        ),
        (
            "Media & Marketing",
            {
                "fields": ("image", ("is_featured", "is_new")),
            },
        ),
    )
