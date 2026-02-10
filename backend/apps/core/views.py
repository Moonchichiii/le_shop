from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from backend.apps.core.models import HeroSlide
from backend.apps.products.selectors import get_featured_products


def home(request: HttpRequest) -> HttpResponse:
    """Render home page with featured products and hero slides."""
    featured = get_featured_products(limit=4)
    hero_slides = HeroSlide.objects.filter(is_active=True).order_by("order")

    context = {
        "featured_products": featured,
        "hero_slides": hero_slides,
    }

    return render(request, "pages/home.html", context)
