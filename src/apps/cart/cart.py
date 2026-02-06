from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from apps.products.models import Product


@dataclass(frozen=True)
class AddResult:
    requested: int
    final: int
    max_stock: int
    clamped: bool
    removed: bool


class Cart:
    SESSION_KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(self.SESSION_KEY)
        if not cart:
            cart = self.session[self.SESSION_KEY] = {}
        self.cart: dict[str, dict[str, Any]] = cart

    def add(
        self, product: Product, quantity: int = 1, override: bool = False
    ) -> AddResult:
        """
        Add/update a product in the cart.
        Server-side clamps to available stock.
        Returns AddResult so views can message correctly.
        """
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {"qty": 0, "price": str(product.price)}

        current_qty = int(self.cart[product_id]["qty"])
        requested = max(int(quantity), 1)

        desired_qty = requested if override else (current_qty + requested)

        max_stock = int(product.stock)

        if max_stock <= 0:
            # can't keep it in the cart
            self.remove(product)
            return AddResult(
                requested=desired_qty,
                final=0,
                max_stock=max_stock,
                clamped=True,
                removed=True,
            )

        final_qty = min(desired_qty, max_stock)
        clamped = final_qty != desired_qty

        # keep >= 1 (since max_stock > 0)
        final_qty = max(1, final_qty)

        self.cart[product_id]["qty"] = final_qty
        self.save()

        return AddResult(
            requested=desired_qty,
            final=final_qty,
            max_stock=max_stock,
            clamped=clamped,
            removed=False,
        )

    def remove(self, product: Product) -> None:
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self) -> None:
        self.session[self.SESSION_KEY] = {}
        self.save()

    def save(self) -> None:
        self.session.modified = True

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids, is_active=True)

        for product in products:
            item = self.cart[str(product.id)]
            item["product"] = product
            item["price"] = Decimal(item["price"])
            item["total_price"] = item["price"] * item["qty"]
            item["max_qty"] = int(product.stock)  # UI hint (still validate server-side)
            yield item

    def __len__(self) -> int:
        return sum(item["qty"] for item in self.cart.values())

    def get_total_price(self) -> Decimal:
        return sum(Decimal(item["price"]) * item["qty"] for item in self.cart.values())
