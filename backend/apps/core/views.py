from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from backend.apps.core.models import HeroSlide, PageSection
from backend.apps.products.models import Product


def home(request: HttpRequest) -> HttpResponse:
    featured = Product.objects.filter(is_active=True, is_featured=True)[:4]
    hero_slides = HeroSlide.objects.filter(is_active=True).order_by("order")
    sections = PageSection.objects.all()
    section_dict = {s.section_type: s for s in sections}

    context = {
        "featured_products": featured,
        "hero_slides": hero_slides,
        "sections": section_dict,
    }

    return render(request, "home.html", context)
