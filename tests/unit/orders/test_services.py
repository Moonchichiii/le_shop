import pytest

from apps.orders.models import Order
from apps.orders.services import reserve_stock_and_create_pending_order


@pytest.mark.django_db
class TestOrderServices:
    def test_reserve_stock_success(self, cart_with_item, product):
        """Test happy path: Stock is decremented, Order created."""
        order, issues = reserve_stock_and_create_pending_order(
            cart_with_item, email="guest@example.com"
        )

        assert order is not None
        assert len(issues) == 0
        assert order.email == "guest@example.com"
        assert order.subtotal == 100.00
        assert order.status == Order.Status.PENDING

        # Verify DB stock decremented
        product.refresh_from_db()
        assert product.stock == 9  # Was 10, bought 1

    def test_reserve_stock_insufficient(self, cart_with_item, product):
        """
        Test the 'Race Condition':
        User adds item to cart (valid), but stock disappears before they checkout.
        """
        # 1. User has 1 item in cart. Stock is 10. All good.
        assert len(cart_with_item) == 1

        # 2. SIMULATE RACE CONDITION:
        # Another process (or admin) sets stock to 0 *after* user added to cart.
        product.stock = 0
        product.save()

        # 3. Now verify the Service Layer catches this discrepancy
        order, issues = reserve_stock_and_create_pending_order(
            cart_with_item, email="fail@example.com"
        )

        # 4. NOW this assertion is valid: The Service blocked the order.
        assert order is None
        assert len(issues) == 1
        assert issues[0].product_id == product.id
        assert issues[0].available == 0

    def test_reserve_stock_inactive_product(self, cart_with_item, product):
        """Test that inactive products are flagged as issues."""
        product.is_active = False
        product.save()

        order, issues = reserve_stock_and_create_pending_order(
            cart_with_item, email="test@example.com"
        )

        assert order is None
        assert len(issues) == 1
        assert issues[0].available == 0

    def test_order_item_creation(self, cart_with_item):
        """Verify OrderItems are created with frozen prices."""
        order, _ = reserve_stock_and_create_pending_order(
            cart_with_item, email="a@b.com"
        )

        # FIX: Mypy needs to know order is real before accessing .items
        assert order is not None

        assert order.items.count() == 1
        item = order.items.first()

        # FIX: Mypy needs to know item is real before accessing .qty
        assert item is not None

        assert item.qty == 1
        assert item.unit_price == 100.00
        assert item.line_total == 100.00
