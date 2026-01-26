import pytest
from django.urls import reverse

from backend.apps.orders.models import Order
from backend.apps.orders.signing import sign_order_id


@pytest.mark.django_db
class TestGuestSecurity:
    def test_guest_receipt_valid_token(self, client):
        order = Order.objects.create(status=Order.Status.PAID, email="guest@test.com")
        token = sign_order_id(order.id)

        url = reverse("guest_order_success", args=[token])
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["order"] == order

    def test_guest_receipt_tampered_token(self, client):
        order = Order.objects.create(status=Order.Status.PAID)
        token = sign_order_id(order.id)

        # Tamper
        url = reverse("guest_order_success", args=[token + "fake"])
        response = client.get(url)

        assert response.status_code == 404

    def test_auth_user_cannot_see_other_user_via_guest_link(
        self, client, django_user_model
    ):
        """
        Security: User A creates order. User B gets the link. User B should NOT see it.
        """
        user_a = django_user_model.objects.create_user(username="UserA", password="pw")
        user_b = django_user_model.objects.create_user(username="UserB", password="pw")

        # Order belongs to A
        order = Order.objects.create(user=user_a, status=Order.Status.PAID)
        token = sign_order_id(order.id)

        # Login as B
        client.force_login(user_b)

        url = reverse("guest_order_success", args=[token])
        response = client.get(url)

        # Should be 404 (Hidden)
        assert response.status_code == 404
