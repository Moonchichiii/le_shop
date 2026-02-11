from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

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

    email = models.EmailField(blank=True, null=True, db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    currency = models.CharField(max_length=10, default="EUR")
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    # ── Provider-agnostic payment fields ──
    payment_provider = models.CharField(max_length=50, blank=True, db_index=True)
    provider_order_id = models.CharField(max_length=255, blank=True, unique=True)
    provider_capture_id = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Order #{self.id} ({self.status})"


# ── OrderItem, OrderTracking, OrderTrackingEvent stay identical ──


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


class OrderTracking(models.Model):
    class FulfillmentStatus(models.TextChoices):
        PROCESSING = "processing", "Processing"
        PACKED = "packed", "Packed"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="tracking"
    )

    status = models.CharField(
        max_length=20,
        choices=FulfillmentStatus.choices,
        default=FulfillmentStatus.PROCESSING,
    )

    carrier = models.CharField(max_length=120, blank=True)
    tracking_number = models.CharField(max_length=120, blank=True)
    delivery_notes = models.TextField(blank=True)

    processing_at = models.DateTimeField(null=True, blank=True)
    packed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_milestone_timestamp(self) -> None:
        now = timezone.now()
        field_map = {
            self.FulfillmentStatus.PROCESSING: "processing_at",
            self.FulfillmentStatus.PACKED: "packed_at",
            self.FulfillmentStatus.SHIPPED: "shipped_at",
            self.FulfillmentStatus.DELIVERED: "delivered_at",
        }
        field = field_map.get(self.status)
        if field and not getattr(self, field):
            setattr(self, field, now)

    def __str__(self) -> str:
        return f"Tracking for Order #{self.order_id} ({self.status})"


class OrderTrackingEvent(models.Model):
    tracking = models.ForeignKey(
        OrderTracking, on_delete=models.CASCADE, related_name="events"
    )

    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_tracking_events",
    )

    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self) -> str:
        return (
            f"{self.from_status} -> {self.to_status} (Order #{self.tracking.order_id})"
        )
