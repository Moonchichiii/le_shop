from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.products.models import Product


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


class OrderTracking(models.Model):
    """
    Fulfillment tracking for an order.
    Kept separate from Order.status (payment lifecycle).
    """

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
        """
        Records the first time we entered each milestone.
        Denormalized timestamps allow simple templates/admin without joins.
        """
        now = timezone.now()
        if self.status == self.FulfillmentStatus.PROCESSING and not self.processing_at:
            self.processing_at = now
        elif self.status == self.FulfillmentStatus.PACKED and not self.packed_at:
            self.packed_at = now
        elif self.status == self.FulfillmentStatus.SHIPPED and not self.shipped_at:
            self.shipped_at = now
        elif self.status == self.FulfillmentStatus.DELIVERED and not self.delivered_at:
            self.delivered_at = now

    def __str__(self) -> str:
        return f"Tracking for Order #{self.order_id} ({self.status})"


class OrderTrackingEvent(models.Model):
    """
    Append-only audit log of fulfillment state changes.
    """

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
