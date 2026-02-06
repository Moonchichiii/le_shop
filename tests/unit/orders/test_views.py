from unittest.mock import patch

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.orders.models import Order


@pytest.mark.django_db
class TestOrderViews:
    @pytest.fixture
    def paypal_mock(self):
        """Mocks the create_order and capture_order calls."""
        with (
            patch("apps.orders.views.create_order") as mock_create,
            patch("apps.orders.views.capture_order") as mock_capture,
        ):
            # Setup successful return values
            mock_create.return_value = {
                "id": "PAYPAL-123",
                "links": [{"rel": "approve", "href": "http://paypal.com/approve"}],
            }

            mock_capture.return_value = {
                "purchase_units": [{"payments": {"captures": [{"id": "CAP-123"}]}}]
            }

            yield mock_create, mock_capture

    def test_checkout_start_redirects_to_paypal(self, client, product, paypal_mock):
        """
        Full Flow: Add to cart -> POST email -> DB Order Created -> Redirect to PayPal
        """
        # 1. Add to cart
        client.post(reverse("cart_add", args=[product.id]), {"qty": 1})

        # 2. Checkout (POST email)
        url = reverse("checkout_start")
        response = client.post(url, {"email": "shopper@test.com"})

        # 3. Verify Order Created
        order = Order.objects.first()
        assert order is not None
        assert order.status == Order.Status.PENDING
        assert order.paypal_order_id == "PAYPAL-123"

        # 4. Verify Redirect
        assert response.status_code == 302
        assert response.url == "http://paypal.com/approve"

    def test_checkout_stock_issue_redirects_cart(self, client, product, paypal_mock):
        """If stock runs out during checkout, redirect back to cart."""
        client.post(reverse("cart_add", args=[product.id]), {"qty": 1})

        # Simulate stock depletion
        product.stock = 0
        product.save()

        response = client.post(reverse("checkout_start"), {"email": "late@test.com"})

        # Should redirect back to cart detail
        assert response.url == reverse("cart_detail")
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("no longer available" in m for m in messages)

    def test_paypal_return_captures_payment(self, client, product, paypal_mock):
        """
        Callback Flow: PayPal redirects back -> Capture funds -> Mark Paid -> Clear Cart
        """
        # 1. Setup Pre-existing Pending Order
        order = Order.objects.create(
            status=Order.Status.PENDING, paypal_order_id="PAYPAL-TOKEN", subtotal=100
        )

        # 2. Call Return URL
        url = reverse("paypal_return") + "?token=PAYPAL-TOKEN"
        response = client.get(url, follow=True)

        # 3. Verify Payment Capture
        order.refresh_from_db()
        assert order.status == Order.Status.PAID
        assert order.paypal_capture_id == "CAP-123"
        assert order.tracking is not None  # Tracking created

        # 4. Verify Success Page content
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("Payment confirmed" in m for m in messages)

        # 5. Cart cleared (client session mock handled by view logic)
        assert "cart" not in client.session or len(client.session["cart"]) == 0

    def test_paypal_return_invalid_token(self, client):
        url = reverse("paypal_return") + "?token=BAD-TOKEN"
        response = client.get(url, follow=True)
        assert response.redirect_chain[-1][0] == reverse("cart_detail")
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("Order not found" in m for m in messages)

    def test_checkout_paypal_api_failure(self, client, product):
        """
        If PayPal API crashes (timeout/error), we should not crash the server.
        We should redirect the user back to the cart with a helpful error.
        """
        client.post(reverse("cart_add", args=[product.id]), {"qty": 1})

        # Mock create_order to raise an Exception (simulate API down)
        with patch("apps.orders.views.create_order") as mock_create:
            mock_create.side_effect = Exception("PayPal is down!")

            response = client.post(
                reverse("checkout_start"), {"email": "test@test.com"}
            )

            # Should NOT be 500 Server Error. Should be 302 Redirect.
            assert response.status_code == 302
            assert response.url == reverse("cart_detail")

            messages = [str(m) for m in get_messages(response.wsgi_request)]
            assert any("Error connecting to PayPal" in m for m in messages)
