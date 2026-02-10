from __future__ import annotations

from django.db.models import Q, QuerySet

from .models import Category, Product


def get_featured_products(*, limit: int = 4) -> QuerySet[Product]:
    return Product.objects.filter(is_active=True, is_featured=True).order_by(
        "-created_at"
    )[:limit]


def get_active_categories() -> QuerySet[Category]:
    return Category.objects.all()


def get_active_products() -> QuerySet[Product]:
    return Product.objects.filter(is_active=True).select_related("category")


def get_filtered_products(
    *,
    category_slug: str = "",
    query: str = "",
) -> QuerySet[Product]:
    qs = get_active_products()

    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))

    return qs


def get_active_product_by_slug(*, slug: str) -> Product:
    # Raises DoesNotExist; view will translate to 404 via get_object_or_404 wrapper
    return Product.objects.get(slug=slug, is_active=True)
