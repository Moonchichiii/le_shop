from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def product_list(request):
    category_slug = (request.GET.get("category") or "").strip()
    q = (request.GET.get("q") or "").strip()

    qs = Product.objects.filter(is_active=True).select_related("category")

    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

    categories = Category.objects.all()

    return render(
        request,
        "products/product_list.html",
        {
            "products": qs,
            "categories": categories,
            "active_category": category_slug,
            "query": q,
        },
    )


def product_detail(request, slug: str):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "products/product_detail.html", {"product": product})
