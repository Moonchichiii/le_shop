from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("settings/", views.settings, name="settings"),
    path("email/", views.email_change, name="email-change"),
    path("danger-zone/", views.danger_zone, name="danger-zone"),
    # addresses
    path("addresses/", views.address_list, name="address-list"),
    path("addresses/new/", views.address_create, name="address-create"),
    path("addresses/<int:pk>/edit/", views.address_update, name="address-update"),
    path("addresses/<int:pk>/delete/", views.address_delete, name="address-delete"),
]
