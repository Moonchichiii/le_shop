from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from backend.apps.products.models import Product


def home(request: HttpRequest) -> HttpResponse:
    featured = Product.objects.filter(is_active=True, is_featured=True)[:4]

    context = {"featured_products": featured}

    return render(request, "home.html", context)
