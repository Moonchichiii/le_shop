from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from backend.apps.products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELED = "canceled", "Canceled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    email = models.EmailField(blank=True)  # for guest checkout later if you want
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    currency = models.CharField(max_length=10, default="EUR")
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    paypal_order_id = models.CharField(max_length=255, blank=True, unique=True)
    paypal_capture_id = models.CharField(max_length=255, blank=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Order #{self.id} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )

    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.product} x{self.qty}"
