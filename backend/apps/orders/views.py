from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from backend.apps.cart.services import Cart

from .models import Order
from .payments.services import get_payment_provider
from .services import reserve_stock_and_create_pending_order
from .signing import sign_order_id, unsign_order_id, unsign_order_track_id
from .tracking_services import get_or_create_tracking


@require_http_methods(["GET", "POST"])
def checkout_start(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.info(request, "Your cart is empty.")
        return redirect("cart_detail")

    user = request.user if request.user.is_authenticated else None
    email = ""

    if not user:
        if request.method == "GET":
            return render(request, "orders/checkout_guest_email.html")

        email = (request.POST.get("email") or "").strip()
        if not email:
            messages.error(request, "Please enter your email to continue.")
            return redirect("checkout_start")

    try:
        order, issues = reserve_stock_and_create_pending_order(
            cart, user=user, email=email
        )
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect("cart_detail")

    if issues:
        for issue in issues:
            if issue.available <= 0:
                messages.warning(
                    request,
                    f"'{issue.product_name}' is no longer available.",
                )
            else:
                messages.warning(
                    request,
                    f"Only {issue.available} left of "
                    f"'{issue.product_name}' — please adjust your quantity.",
                )
        return redirect("cart_detail")

    assert order is not None

    return_url = request.build_absolute_uri(reverse("payment_return"))
    cancel_url = request.build_absolute_uri(reverse("payment_cancel"))

    provider = get_payment_provider()

    try:
        result = provider.create_payment(
            order=order,
            return_url=return_url,
            cancel_url=cancel_url,
        )
    except Exception:
        messages.error(
            request,
            "Error connecting to PayPal. Please try again.",
        )
        return redirect("cart_detail")

    order.payment_provider = provider.slug
    order.provider_order_id = result.provider_order_id
    order.save(update_fields=["payment_provider", "provider_order_id"])

    if not result.redirect_url:
        messages.error(
            request,
            "Payment provider did not return an approval link.",
        )
        return redirect("cart_detail")

    return redirect(result.redirect_url)


def payment_return(request: HttpRequest) -> HttpResponse:
    provider_order_id = (request.GET.get("token") or "").strip()

    if not provider_order_id:
        messages.error(request, "Missing payment token.")
        return redirect("cart_detail")

    try:
        order = Order.objects.get(provider_order_id=provider_order_id)
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect("cart_detail")

    if order.status != Order.Status.PAID:
        provider = get_payment_provider()

        try:
            capture = provider.capture_payment(
                provider_order_id=provider_order_id,
            )
        except Exception:
            messages.error(
                request,
                "Payment capture failed. Please contact support.",
            )
            return redirect("cart_detail")

        order.status = Order.Status.PAID
        order.provider_capture_id = capture.capture_id  # ← CaptureResult
        order.save(update_fields=["status", "provider_capture_id"])

        get_or_create_tracking(order)

    Cart(request).clear()

    messages.success(
        request,
        f"Payment confirmed! Order #{order.id} is being processed.",
    )

    if order.user_id:
        return redirect("orders_list")

    token = sign_order_id(order.id)
    return redirect("guest_order_success", token=token)


def payment_cancel(request: HttpRequest) -> HttpResponse:
    messages.info(request, "Payment process cancelled.")
    return redirect("cart_detail")


def guest_order_success(request, token: str):
    order_id = unsign_order_id(token, max_age_seconds=86400)

    if not order_id:
        raise Http404("Invalid or expired order link.")

    order = get_object_or_404(Order, id=order_id)

    if order.user_id and (
        not request.user.is_authenticated or order.user_id != request.user.id
    ):
        raise Http404()

    return render(
        request,
        "orders/order_confirmation_guest.html",
        {"order": order},
    )


@login_required
def orders_list(request):
    orders_qs = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items", "items__product")
        .order_by("-created_at")
    )

    paginator = Paginator(orders_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)
    qs = params.urlencode()
    if qs:
        qs += "&"

    context = {
        "page_obj": page_obj,
        "orders": page_obj.object_list,
        "qs": qs,
        "hx_target_id": "orders-fragment",
    }

    template = (
        "orders/_list_fragment.html"
        if getattr(request, "htmx", False)
        else "orders/order_list.html"
    )
    return render(request, template, context)


@login_required
def order_track(request, order_id: int) -> HttpResponse:
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "items__product"),
        id=order_id,
        user=request.user,
    )

    tracking = get_or_create_tracking(order)
    if tracking is None:
        messages.info(request, "Payment not confirmed yet.")
        return redirect("orders_list")

    events = tracking.events.all()

    return render(
        request,
        "orders/order_tracking.html",
        {"order": order, "tracking": tracking, "events": events},
    )


def guest_order_track(request, token: str) -> HttpResponse:
    order_id = unsign_order_track_id(token, max_age_seconds=60 * 60 * 24 * 30)
    if not order_id:
        raise Http404("Invalid or expired tracking link.")

    order = get_object_or_404(
        Order.objects.prefetch_related("items", "items__product"),
        id=order_id,
    )

    if order.user_id and (
        not request.user.is_authenticated or order.user_id != request.user.id
    ):
        raise Http404()

    tracking = get_or_create_tracking(order)
    if tracking is None:
        raise Http404("Tracking not available.")

    events = tracking.events.all()

    return render(
        request,
        "orders/order_tracking.html",
        {"order": order, "tracking": tracking, "events": events},
    )
