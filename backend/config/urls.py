from django.contrib import admin
from django.urls import include, path

from backend.apps.core.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    # Root -> Core Logic
    path("", home, name="home"),
    path("accounts/", include("allauth.urls")),
    path("shop/", include("backend.apps.products.urls")),
    path("cart/", include("backend.apps.cart.urls")),
    path("", include("backend.apps.orders.urls")),
]
