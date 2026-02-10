from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Product
from .selectors import get_active_categories, get_filtered_products


def product_list(request):
    category_slug = (request.GET.get("category") or "").strip()
    q = (request.GET.get("q") or "").strip()

    products_qs = get_filtered_products(category_slug=category_slug, query=q)
    categories = get_active_categories()

    paginator = Paginator(products_qs, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Build querystring WITHOUT page, for clean pagination links
    params = request.GET.copy()
    params.pop("page", None)
    qs = params.urlencode()
    if qs:
        qs += "&"

    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": categories,
        "active_category": category_slug,
        "query": q,
        "qs": qs,
        "hx_target_id": "products-fragment",
    }

    template = (
        "products/_list_fragment.html"
        if getattr(request, "htmx", False)
        else "products/product_list.html"
    )
    return render(request, template, context)


def product_detail(request, slug: str):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "products/product_detail.html", {"product": product})
