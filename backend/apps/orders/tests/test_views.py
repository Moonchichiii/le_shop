from unittest.mock import MagicMock, patch

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from backend.apps.orders.models import Order
from backend.apps.orders.payments.base import CaptureResult, PaymentResult


@pytest.mark.django_db
class TestOrderViews:
    @pytest.fixture
    def provider_mock(self):
        """Mocks the payment provider returned by get_payment_provider()."""
        mock_provider = MagicMock()
        mock_provider.slug = "test"

        mock_provider.create_payment.return_value = PaymentResult(
            approved=True,
            provider_order_id="PROVIDER-123",
            redirect_url="http://provider.com/approve",
        )

        mock_provider.capture_payment.return_value = CaptureResult(
            approved=True,
            capture_id="CAP-123",
        )

        with patch(
            "backend.apps.orders.views.get_payment_provider",
            return_value=mock_provider,
        ):
            yield mock_provider

    def test_checkout_start_redirects_to_provider(self, client, product, provider_mock):
        client.post(reverse("cart_add", args=[product.id]), {"qty": 1})

        url = reverse("checkout_start")
        response = client.post(url, {"email": "shopper@test.com"})

        order = Order.objects.first()
        assert order is not None
        assert order.status == Order.Status.PENDING
        assert order.provider_order_id == "PROVIDER-123"
        assert order.payment_provider == "test"

        assert response.status_code == 302
        assert response.url == "http://provider.com/approve"

    def test_checkout_stock_issue_redirects_cart(self, client, product, provider_mock):
        client.post(reverse("cart_add", args=[product.id]), {"qty": 1})

        product.stock = 0
        product.save()

        response = client.post(reverse("checkout_start"), {"email": "late@test.com"})

        assert response.url == reverse("cart_detail")
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("no longer available" in m for m in msgs)

    def test_payment_return_captures(self, client, product, provider_mock):
        order = Order.objects.create(
            status=Order.Status.PENDING,
            provider_order_id="PROVIDER-TOKEN",
            subtotal=100,
        )

        url = reverse("payment_return") + "?token=PROVIDER-TOKEN"
        response = client.get(url, follow=True)

        order.refresh_from_db()
        assert order.status == Order.Status.PAID
        assert order.provider_capture_id == "CAP-123"
        assert order.tracking is not None

        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("Payment confirmed" in m for m in msgs)

        assert "cart" not in client.session or len(client.session["cart"]) == 0

    def test_payment_return_invalid_token(self, client):
        url = reverse("payment_return") + "?token=BAD-TOKEN"
        response = client.get(url, follow=True)
        assert response.redirect_chain[-1][0] == reverse("cart_detail")
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("Order not found" in m for m in msgs)

    def test_checkout_provider_api_failure(self, client, product):
        client.post(reverse("cart_add", args=[product.id]), {"qty": 1})

        mock_provider = MagicMock()
        mock_provider.slug = "test"
        mock_provider.create_payment.side_effect = Exception("API down!")

        with patch(
            "backend.apps.orders.views.get_payment_provider",
            return_value=mock_provider,
        ):
            response = client.post(
                reverse("checkout_start"), {"email": "test@test.com"}
            )

            assert response.status_code == 302
            assert response.url == reverse("cart_detail")

            msgs = [str(m) for m in get_messages(response.wsgi_request)]
            assert any("Error connecting" in m for m in msgs)
