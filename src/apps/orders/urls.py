from django.urls import path

from . import views

urlpatterns = [
    path("checkout/", views.checkout_start, name="checkout_start"),
    # PayPal Callbacks
    path("paypal/return/", views.paypal_return, name="paypal_return"),
    path("paypal/cancel/", views.paypal_cancel, name="paypal_cancel"),
    # Account Views
    path("orders/", views.orders_list, name="orders_list"),
    path("orders/<int:order_id>/track/", views.order_track, name="order_track"),
    # Guest Views (Signed Access)
    path(
        "order/receipt/<str:token>/",
        views.guest_order_success,
        name="guest_order_success",
    ),
    path("order/track/<str:token>/", views.guest_order_track, name="guest_order_track"),
]
