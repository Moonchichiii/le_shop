import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from backend.apps.products.models import Category, Product


@pytest.mark.django_db
class TestCartViews:
    @pytest.fixture
    def product(self):
        category = Category.objects.create(name="Test Cat", slug="test-cat")
        return Product.objects.create(
            category=category,
            name="Test Product",
            slug="test-product",
            price=50.00,
            stock=10,
            is_active=True,
        )

    def test_cart_detail_empty(self, client):
        url = reverse("cart_detail")
        response = client.get(url)
        assert response.status_code == 200
        assert "cart" in response.context
        assert len(response.context["cart"]) == 0

    def test_cart_add_happy_path(self, client, product):
        url = reverse("cart_add", args=[product.id])
        data = {"qty": 2}
        response = client.post(url, data, follow=True)

        assert response.status_code == 200

        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert "Added to cart." in messages[0]  # First message is fine here

        cart_in_context = response.context["cart"]
        assert len(cart_in_context) == 2

    def test_cart_add_clamped_stock(self, client, product):
        url = reverse("cart_add", args=[product.id])
        data = {"qty": 20}
        response = client.post(url, data, follow=True)

        # Check any message in the list
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("Only 10 left" in m for m in messages)

        cart_in_context = response.context["cart"]
        assert len(cart_in_context) == 10

    def test_cart_update_override(self, client, product):
        add_url = reverse("cart_add", args=[product.id])
        client.post(add_url, {"qty": 5})

        update_url = reverse("cart_update", args=[product.id])
        response = client.post(update_url, {"qty": 3}, follow=True)

        cart_in_context = response.context["cart"]
        assert len(cart_in_context) == 3

        # FIX: Check if ANY message contains the text
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("Cart updated" in m for m in messages)

    def test_cart_remove(self, client, product):
        client.post(reverse("cart_add", args=[product.id]), {"qty": 1})

        url = reverse("cart_remove", args=[product.id])
        response = client.post(url, follow=True)

        cart_in_context = response.context["cart"]
        assert len(cart_in_context) == 0

        # FIX: Check if ANY message contains the text
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("Removed" in m for m in messages)

    def test_cart_add_invalid_product_404(self, client):
        url = reverse("cart_add", args=[9999])
        response = client.post(url, {"qty": 1})
        assert response.status_code == 404
