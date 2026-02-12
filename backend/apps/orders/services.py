from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from backend.apps.cart.services import Cart
from backend.apps.products.models import Product

from .models import Order, OrderItem


@dataclass(frozen=True)
class StockIssue:
    product_id: int
    product_name: str
    requested: int
    available: int


@transaction.atomic
def reserve_stock_and_create_pending_order(
    cart: Cart,
    *,
    user: Any = None,
    email: str = "",
) -> tuple[Order | None, list[StockIssue]]:
    """
    Authoritative "checkout begin":
    - locks products (deterministic order)
    - re-checks stock under lock
    - decrements stock (atomic guard + is_active check)
    - creates Order + OrderItems

    Returns (order, issues).
    Raises ValidationError on integrity failure to trigger rollback.
    """
    if len(cart) == 0:
        return None, []

    # 1. Deduplicate & Sort IDs (Deterministic locking prevents deadlocks)
    product_ids = sorted({int(pid) for pid in cart.cart})

    # 2. Lock rows
    products = (
        Product.objects.select_for_update().filter(id__in=product_ids).order_by("id")
    )
    product_map = {p.id: p for p in products}

    issues: list[StockIssue] = []

    # 3. Validation Phase
    for pid_str, data in cart.cart.items():
        pid = int(pid_str)
        qty = int(data.get("qty", 0))
        product = product_map.get(pid)

        if not product or not product.is_active:
            issues.append(
                StockIssue(
                    product_id=pid,
                    product_name=getattr(product, "name", "Unknown item"),
                    requested=qty,
                    available=0,
                )
            )
            continue

        available = int(product.stock)
        if qty < 1 or qty > available:
            issues.append(
                StockIssue(
                    product_id=product.id,
                    product_name=product.name,
                    requested=qty,
                    available=available,
                )
            )

    if issues:
        return None, issues

    # 4. Create Order
    order = Order.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        email=email
        or (
            getattr(user, "email", "")
            if getattr(user, "is_authenticated", False)
            else ""
        ),
        status=Order.Status.PENDING,
        currency="EUR",
        subtotal=cart.get_total_price(),
    )

    # 5. Decrement Phase (Atomic Update)
    for item in cart:
        pid = int(item["product"].id)
        qty = int(item["qty"])
        unit_price = item["price"]
        line_total = item["total_price"]

        locked_product = product_map.get(pid)

        if not locked_product or not locked_product.is_active:
            raise ValidationError(
                f"Integrity error: Product {pid} missing or inactive under lock."
            )

        updated_count = Product.objects.filter(
            pk=locked_product.pk,
            is_active=True,
            stock__gte=qty,
        ).update(stock=F("stock") - qty)

        if updated_count == 0:
            raise ValidationError(
                "Critical integrity error: Could not decrement stock "
                f"for product {pid}. "
                "Stock changed unexpectedly."
            )

        OrderItem.objects.create(
            order=order,
            product=locked_product,
            qty=qty,
            unit_price=unit_price,
            line_total=line_total,
        )

    return order, []
