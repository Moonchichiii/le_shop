from django.contrib import admin
from django.urls import include, path

from backend.apps.core import views as core_views

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("account/", include("backend.apps.accounts.urls")),
    path("shop/", include("backend.apps.products.urls")),
    path("cart/", include("backend.apps.cart.urls")),
    path("orders/", include("backend.apps.orders.urls")),
    path("", include("backend.apps.core.urls")),
    path("mock-paypal-approve", core_views.mock_paypal_approve),
]
