from django.contrib import admin
from django.urls import include, path

from apps.core.views import home

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin/", admin.site.urls),
    # Root -> Core Logic
    path("", home, name="home"),
    path("accounts/", include("allauth.urls")),
    path("shop/", include("apps.products.urls")),
    path("cart/", include("apps.cart.urls")),
    path("", include("apps.orders.urls")),
]
