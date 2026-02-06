from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.products.models import Product

from .cart import Cart


def cart_detail(request):
    cart = Cart(request)
    return render(request, "cart/detail.html", {"cart": cart})


@require_POST
def cart_add(request, product_id: int):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)

    try:
        qty = int(request.POST.get("qty", 1))
    except ValueError:
        qty = 1

    result = cart.add(product=product, quantity=qty, override=False)

    if result.removed:
        messages.warning(request, f"Sorry, '{product.name}' is sold out.")
    elif result.clamped:
        messages.info(
            request, f"Only {result.max_stock} left — quantity updated in your cart."
        )
    else:
        messages.success(request, "Added to cart.")

    return redirect("cart_detail")


@require_POST
def cart_update(request, product_id: int):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)

    try:
        qty = int(request.POST.get("qty", 1))
    except ValueError:
        qty = 1

    result = cart.add(product=product, quantity=qty, override=True)

    if result.removed:
        messages.warning(request, f"'{product.name}' is now sold out and was removed.")
    elif result.clamped:
        messages.info(
            request,
            f"Only {result.max_stock} left — quantity updated to {result.final}.",
        )
    else:
        messages.success(request, "Cart updated.")

    return redirect("cart_detail")


@require_POST
def cart_remove(request, product_id: int):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart.remove(product)
    messages.success(request, f"Removed '{product.name}' from cart.")
    return redirect("cart_detail")
