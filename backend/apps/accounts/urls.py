from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("settings/", views.settings, name="settings"),
    path("email/", views.email_change, name="email-change"),
    path("danger-zone/", views.danger_zone, name="danger-zone"),
]
