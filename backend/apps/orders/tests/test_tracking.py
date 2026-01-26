import pytest

from backend.apps.orders.models import Order, OrderTracking
from backend.apps.orders.tracking_services import (
    get_or_create_tracking,
    update_tracking_status,
)


@pytest.mark.django_db
class TestTrackingService:
    @pytest.fixture
    def paid_order(self, product):
        """Helper to create a paid order (tracking requires paid status)."""
        order = Order.objects.create(email="test@test.com", status=Order.Status.PAID)
        return order

    def test_tracking_created_automatically_on_paid(self, paid_order):
        tracking = get_or_create_tracking(paid_order)
        assert tracking is not None
        assert tracking.status == OrderTracking.FulfillmentStatus.PROCESSING
        # Timestamp should be set
        assert tracking.processing_at is not None

    def test_update_status_happy_path(self, paid_order):
        tracking, issues = update_tracking_status(
            order=paid_order, new_status=OrderTracking.FulfillmentStatus.PACKED
        )
        assert len(issues) == 0
        assert tracking.status == OrderTracking.FulfillmentStatus.PACKED
        assert tracking.packed_at is not None

        # Verify Audit Log
        assert tracking.events.count() == 1
        event = tracking.events.first()
        assert event.from_status == "processing"
        assert event.to_status == "packed"

    def test_update_status_invalid_transition(self, paid_order):
        """Cannot jump from Processing directly to Delivered."""
        tracking, issues = update_tracking_status(
            order=paid_order, new_status=OrderTracking.FulfillmentStatus.DELIVERED
        )
        assert tracking is None
        assert len(issues) == 1
        assert issues[0].code == "invalid_transition"

    def test_update_unpaid_order_fails(self):
        unpaid = Order.objects.create(status=Order.Status.PENDING)
        tracking, issues = update_tracking_status(order=unpaid, new_status="packed")
        assert tracking is None
        assert issues[0].code == "not_paid"
