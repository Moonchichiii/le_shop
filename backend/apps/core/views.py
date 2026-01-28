from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from backend.apps.core.models import HeroSlide
from backend.apps.products.models import Product


def home(request: HttpRequest) -> HttpResponse:
    featured = Product.objects.filter(is_active=True, is_featured=True)[:4]
    hero_slides = HeroSlide.objects.filter(is_active=True).order_by("order")

    context = {
        "featured_products": featured,
        "hero_slides": hero_slides,
    }

    return render(request, "home.html", context)
