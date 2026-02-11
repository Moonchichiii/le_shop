from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.apps.orders.models import Order


@dataclass(frozen=True)
class PaymentResult:
    """Returned by create_payment()."""

    approved: bool
    provider_order_id: str
    redirect_url: str | None = None


@dataclass(frozen=True)
class CaptureResult:
    """Returned by capture_payment()."""

    approved: bool
    capture_id: str


class PaymentProvider(ABC):
    """
    Every concrete provider must declare a unique `slug`
    and implement create + capture.
    """

    slug: str = ""

    @abstractmethod
    def create_payment(
        self,
        *,
        order: Order,
        return_url: str,
        cancel_url: str,
    ) -> PaymentResult: ...

    @abstractmethod
    def capture_payment(
        self,
        *,
        provider_order_id: str,
    ) -> CaptureResult: ...
