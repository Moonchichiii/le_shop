# backend/apps/orders/urls.py  (no changes)

from django.urls import path

from . import views

urlpatterns = [
    path("checkout/", views.checkout_start, name="checkout_start"),
    path("payment/return/", views.payment_return, name="payment_return"),
    path("payment/cancel/", views.payment_cancel, name="payment_cancel"),
    path("orders/", views.orders_list, name="orders_list"),
    path(
        "orders/<int:order_id>/track/",
        views.order_track,
        name="order_track",
    ),
    path(
        "order/receipt/<str:token>/",
        views.guest_order_success,
        name="guest_order_success",
    ),
    path(
        "order/track/<str:token>/",
        views.guest_order_track,
        name="guest_order_track",
    ),
]
