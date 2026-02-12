from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction

from .models import Order, OrderTracking, OrderTrackingEvent


@dataclass(frozen=True)
class TrackingIssue:
    code: str
    message: str


_ALLOWED_NEXT: dict[str, set[str]] = {
    OrderTracking.FulfillmentStatus.PROCESSING: {
        OrderTracking.FulfillmentStatus.PACKED
    },
    OrderTracking.FulfillmentStatus.PACKED: {OrderTracking.FulfillmentStatus.SHIPPED},
    OrderTracking.FulfillmentStatus.SHIPPED: {
        OrderTracking.FulfillmentStatus.DELIVERED
    },
    OrderTracking.FulfillmentStatus.DELIVERED: set(),
}


@transaction.atomic
def get_or_create_tracking(order: Order) -> OrderTracking | None:
    """
    Paid-only creation:
    - If order is PAID: create lazily (idempotent) and ensure initial timestamp.
    - If order is NOT PAID: do NOT create. Return existing tracking if it exists.
    """
    if order.status != Order.Status.PAID:
        return OrderTracking.objects.filter(order=order).first()

    tracking, _ = OrderTracking.objects.select_for_update().get_or_create(order=order)

    if (
        tracking.status == OrderTracking.FulfillmentStatus.PROCESSING
        and not tracking.processing_at
    ):
        tracking.set_milestone_timestamp()
        tracking.save(update_fields=["processing_at", "updated_at"])

    return tracking


@transaction.atomic
def update_tracking_status(
    *,
    order: Order,
    actor: Any = None,
    new_status: str,
    carrier: str = "",
    tracking_number: str = "",
    delivery_notes: str = "",
    note: str = "",
) -> tuple[OrderTracking | None, list[TrackingIssue]]:
    """
    Updates fulfillment tracking for a paid order.
    Designed for staff/admin flows (view/admin should handle permissions).
    """
    if order.status == Order.Status.CANCELED:
        return None, [
            TrackingIssue(
                code="canceled",
                message="Tracking cannot be updated for canceled orders.",
            )
        ]

    if order.status != Order.Status.PAID:
        return None, [
            TrackingIssue(
                code="not_paid",
                message="Tracking can only be updated for paid orders.",
            )
        ]

    tracking = get_or_create_tracking(order)
    if tracking is None:
        return None, [
            TrackingIssue(
                code="missing_tracking",
                message="Tracking could not be created for this order.",
            )
        ]

    current = tracking.status
    if new_status != current:
        allowed = _ALLOWED_NEXT.get(current, set())
        if new_status not in allowed:
            return None, [
                TrackingIssue(
                    code="invalid_transition",
                    message=f"Cannot move from '{current}' to '{new_status}'.",
                )
            ]

        OrderTrackingEvent.objects.create(
            tracking=tracking,
            from_status=current,
            to_status=new_status,
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            note=note.strip(),
        )
        tracking.status = new_status

    tracking.carrier = carrier.strip()
    tracking.tracking_number = tracking_number.strip()
    tracking.delivery_notes = delivery_notes.strip()

    tracking.set_milestone_timestamp()
    tracking.save()

    return tracking, []
