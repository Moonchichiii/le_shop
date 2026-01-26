from django.contrib import admin
from unfold.admin import ModelAdmin  # type: ignore

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "qty", "unit_price", "line_total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("id", "status", "email", "subtotal", "currency", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "email", "paypal_order_id", "paypal_capture_id")
    inlines = [OrderItemInline]
    ordering = ("-created_at",)
    readonly_fields = (
        "paypal_order_id",
        "paypal_capture_id",
        "created_at",
        "updated_at",
    )
