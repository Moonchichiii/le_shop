from typing import Any

from django.contrib import admin
from django.http import HttpRequest
from unfold.admin import ModelAdmin  # type: ignore

from .models import Order, OrderItem, OrderTracking, OrderTrackingEvent


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "qty", "unit_price", "line_total")
    can_delete = False


class OrderTrackingInline(admin.StackedInline):
    model = OrderTracking
    extra = 0
    can_delete = False
    fields = (
        "status",
        "carrier",
        "tracking_number",
        "delivery_notes",
        "processing_at",
        "packed_at",
        "shipped_at",
        "delivered_at",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "processing_at",
        "packed_at",
        "shipped_at",
        "delivered_at",
        "created_at",
        "updated_at",
    )


class OrderTrackingEventInline(admin.TabularInline):
    model = OrderTrackingEvent
    extra = 0
    can_delete = False
    readonly_fields = ("from_status", "to_status", "actor", "note", "created_at")

    def has_add_permission(self, request: HttpRequest, obj: Any | None = None) -> bool:
        return False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "id",
        "status",
        "payment_provider",
        "email",
        "subtotal",
        "currency",
        "created_at",
    )
    list_filter = ("status", "payment_provider", "created_at")
    search_fields = (
        "id",
        "email",
        "provider_order_id",
        "provider_capture_id",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "payment_provider",
        "provider_order_id",
        "provider_capture_id",
        "created_at",
        "updated_at",
    )
    inlines = [OrderTrackingInline, OrderItemInline]


@admin.register(OrderTracking)
class OrderTrackingAdmin(ModelAdmin):
    list_display = ("order", "status", "carrier", "tracking_number", "updated_at")
    list_filter = ("status", "updated_at")
    search_fields = ("order__id", "order__email", "carrier", "tracking_number")
    ordering = ("-updated_at",)
    inlines = [OrderTrackingEventInline]
    readonly_fields = (
        "processing_at",
        "packed_at",
        "shipped_at",
        "delivered_at",
        "created_at",
        "updated_at",
    )
