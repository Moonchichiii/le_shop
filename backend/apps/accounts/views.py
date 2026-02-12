from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AddressForm, ProfileForm
from .models import Address, CustomerProfile, User


def _get_owned_address(*, request: HttpRequest, pk: int) -> Address:
    # Ensure user is authenticated for type checking
    if not request.user.is_authenticated:
        raise Http404

    address = get_object_or_404(Address, pk=pk)
    if address.user_id != request.user.id:
        raise Http404
    return address


@login_required
def settings(request: HttpRequest) -> HttpResponse:
    user = cast(User, request.user)
    profile, _ = CustomerProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Settings updated.")
            return redirect("accounts:settings")
    else:
        profile_form = ProfileForm(instance=profile)

    return render(
        request,
        "accounts/settings.html",
        {
            "profile_form": profile_form,
        },
    )


@login_required
def address_list(request: HttpRequest) -> HttpResponse:
    user = cast(User, request.user)
    addresses = Address.objects.filter(user=user)
    return render(request, "accounts/addresses_list.html", {"addresses": addresses})


@login_required
def address_create(request: HttpRequest) -> HttpResponse:
    user = cast(User, request.user)
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            addr: Address = form.save(commit=False)
            addr.user = user

            if addr.is_default:
                Address.objects.filter(user=user, is_default=True).update(
                    is_default=False
                )

            addr.save()
            messages.success(request, "Address saved.")
            return redirect("accounts:address-list")
    else:
        form = AddressForm()

    return render(
        request, "accounts/address_form.html", {"form": form, "mode": "create"}
    )


@login_required
def address_update(request: HttpRequest, pk: int) -> HttpResponse:
    user = cast(User, request.user)
    addr = _get_owned_address(request=request, pk=pk)

    if request.method == "POST":
        form = AddressForm(request.POST, instance=addr)
        if form.is_valid():
            addr = form.save(commit=False)
            if addr.is_default:
                Address.objects.filter(user=user, is_default=True).exclude(
                    pk=addr.pk
                ).update(is_default=False)
            addr.save()
            messages.success(request, "Address updated.")
            return redirect("accounts:address-list")
    else:
        form = AddressForm(instance=addr)

    return render(
        request, "accounts/address_form.html", {"form": form, "mode": "update"}
    )


@login_required
def address_delete(request: HttpRequest, pk: int) -> HttpResponse:
    addr = _get_owned_address(request=request, pk=pk)

    if request.method == "POST":
        addr.delete()
        messages.success(request, "Address deleted.")
        return redirect("accounts:address-list")

    return render(request, "accounts/address_confirm_delete.html", {"address": addr})


@login_required
def email_change(request: HttpRequest) -> HttpResponse:
    return render(request, "accounts/email_change.html")


@login_required
def danger_zone(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        if request.POST.get("confirmation") == "DELETE":
            # Capture user before logout
            user = cast(User, request.user)
            from django.contrib.auth import logout

            logout(request)
            user.delete()
            messages.success(request, "Your account has been deleted.")
            return redirect("core:home")
        else:
            messages.error(request, 'Please type "DELETE" to confirm.')

    return render(request, "accounts/danger_zone.html")
