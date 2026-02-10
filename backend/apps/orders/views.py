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
from .paypal import capture_order, create_order
from .services import reserve_stock_and_create_pending_order
from .signing import sign_order_id, unsign_order_id, unsign_order_track_id
from .tracking_services import get_or_create_tracking


@require_http_methods(["GET", "POST"])
def checkout_start(request):
    """
    1. Collect Email (if guest)
    2. Reserve Stock (Atomic)
    3. Create PayPal Order
    4. Redirect to PayPal
    """
    cart = Cart(request)

    if len(cart) == 0:
        messages.info(request, "Your cart is empty.")
        return redirect("cart_detail")

    # --- Step 1: User/Email ---
    user = request.user if request.user.is_authenticated else None
    email = ""

    if not user:
        if request.method == "GET":
            return render(request, "orders/guest_email.html")

        email = (request.POST.get("email") or "").strip()
        if not email:
            messages.error(request, "Please enter your email to continue.")
            return redirect("checkout_start")

    # --- Step 2: Reserve Stock ---
    try:
        order, issues = reserve_stock_and_create_pending_order(
            cart, user=user, email=email
        )
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect("cart_detail")

    # Handle Stock Issues
    if issues:
        for issue in issues:
            if issue.available <= 0:
                messages.warning(
                    request, f"'{issue.product_name}' is no longer available."
                )
            else:
                messages.warning(
                    request,
                    (
                        f"Only {issue.available} left of '{issue.product_name}' — "
                        "please adjust your quantity."
                    ),
                )
        return redirect("cart_detail")

    assert order is not None

    # --- Step 3: PayPal Integration ---
    return_url = request.build_absolute_uri(reverse("paypal_return"))
    cancel_url = request.build_absolute_uri(reverse("paypal_cancel"))

    try:
        pp_data = create_order(
            total_eur=str(order.subtotal),
            reference_id=str(order.id),
            return_url=return_url,
            cancel_url=cancel_url,
        )
    except Exception:
        messages.error(request, "Error connecting to PayPal. Please try again.")
        # If API fails, we redirect to cart (stock is technically reserved pending
        # expiry)
        return redirect("cart_detail")

    # Save PayPal Order ID
    order.paypal_order_id = pp_data["id"]
    order.save(update_fields=["paypal_order_id"])

    # Find the approval link
    approval_url = next(
        (
            link["href"]
            for link in pp_data.get("links", [])
            if link.get("rel") == "approve"
        ),
        None,
    )

    if not approval_url:
        messages.error(request, "PayPal did not return an approval link.")
        return redirect("cart_detail")

    # Do NOT clear cart yet. Wait for capture.
    return redirect(approval_url)


def paypal_return(request: HttpRequest) -> HttpResponse:
    """
    Callback after user approves payment on PayPal.
    Captures funds -> Updates Order -> Clears Cart -> Redirects.
    """
    paypal_order_id = (request.GET.get("token") or "").strip()

    if not paypal_order_id:
        messages.error(request, "Missing PayPal token.")
        return redirect("cart_detail")

    # 1. Find Order
    try:
        order = Order.objects.get(paypal_order_id=paypal_order_id)
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect("cart_detail")

    # 2. Capture Payment (if not already paid)
    if order.status != Order.Status.PAID:
        try:
            data = capture_order(paypal_order_id)
        except Exception:
            messages.error(request, "Payment capture failed. Please contact support.")
            return redirect("cart_detail")

        # Extract Capture ID
        capture_id = ""
        purchase_units = data.get("purchase_units") or []
        if purchase_units:
            captures = purchase_units[0].get("payments", {}).get("captures", [])
            if captures:
                capture_id = captures[0].get("id", "")

        order.status = Order.Status.PAID
        order.paypal_capture_id = capture_id
        order.save(update_fields=["status", "paypal_capture_id"])

        # Ensure tracking exists immediately after payment capture (idempotent)
        get_or_create_tracking(order)

    # 3. Clear Cart (Success)
    Cart(request).clear()

    messages.success(
        request, f"Payment confirmed! Order #{order.id} is being processed."
    )

    # 4. Redirect: Split Logic
    if order.user_id:
        # Authenticated User -> Standard Account View
        return redirect("orders_list")

    # Guest User -> Signed Token View
    token = sign_order_id(order.id)
    return redirect("guest_order_success", token=token)


def paypal_cancel(request: HttpRequest) -> HttpResponse:
    messages.info(request, "Payment process cancelled.")
    return redirect("cart_detail")


def guest_order_success(request, token: str):
    """
    Secure view for guests to see their receipt.
    Validates the token to ensure they are authorized to see this specific order.
    """
    order_id = unsign_order_id(token, max_age_seconds=86400)  # Valid for 24h

    if not order_id:
        raise Http404("Invalid or expired order link.")

    order = get_object_or_404(Order, id=order_id)

    # Security Check:
    # If the order belongs to a registered user, ensure the current request
    # comes from that user. Prevents token leakage or cross-user viewing.
    if order.user_id and (
        not request.user.is_authenticated or order.user_id != request.user.id
    ):
        raise Http404()

    return render(request, "orders/guest_success.html", {"order": order})


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
        "orders/order_track.html",
        {"order": order, "tracking": tracking, "events": events},
    )


def guest_order_track(request, token: str) -> HttpResponse:
    order_id = unsign_order_track_id(token, max_age_seconds=60 * 60 * 24 * 30)
    if not order_id:
        raise Http404("Invalid or expired tracking link.")

    order = get_object_or_404(
        Order.objects.prefetch_related("items", "items__product"), id=order_id
    )

    # If the order belongs to a registered user, do not allow token-only access.
    if order.user_id and (
        not request.user.is_authenticated or order.user_id != request.user.id
    ):
        raise Http404()

    tracking = get_or_create_tracking(order)
    if tracking is None:
        # Don't create tracking for unpaid orders; for guests we just 404
        raise Http404("Tracking not available.")

    events = tracking.events.all()

    return render(
        request,
        "orders/order_track.html",
        {"order": order, "tracking": tracking, "events": events},
    )
