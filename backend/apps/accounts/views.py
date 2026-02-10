from django.shortcuts import render


def settings(request):
    return render(request, "accounts/settings.html")


def email_change(request):
    return render(request, "accounts/email_change.html")


def danger_zone(request):
    return render(request, "accounts/danger_zone.html")
