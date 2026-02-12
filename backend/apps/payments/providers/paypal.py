from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings

from backend.apps.orders.models import Order
from backend.apps.payments.base import CaptureResult, PaymentProvider, PaymentResult


@dataclass(frozen=True)
class _PayPalConfig:
    base_url: str
    client_id: str
    client_secret: str


def _paypal_config() -> _PayPalConfig:
    env = (getattr(settings, "PAYPAL_ENV", "sandbox") or "sandbox").lower()
    base_url = (
        "https://api-m.sandbox.paypal.com"
        if env == "sandbox"
        else "https://api-m.paypal.com"
    )
    return _PayPalConfig(
        base_url=base_url,
        client_id=settings.PAYPAL_CLIENT_ID,
        client_secret=settings.PAYPAL_CLIENT_SECRET,
    )


def _get_access_token() -> str:
    cfg = _paypal_config()
    r = requests.post(
        f"{cfg.base_url}/v1/oauth2/token",
        auth=(cfg.client_id, cfg.client_secret),
        data={"grant_type": "client_credentials"},
        timeout=20,
    )
    r.raise_for_status()
    return str(r.json()["access_token"])


def _create_paypal_order(
    *,
    total_eur: str,
    reference_id: str,
    return_url: str,
    cancel_url: str,
) -> dict[str, Any]:
    cfg = _paypal_config()
    token = _get_access_token()

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": reference_id,
                "amount": {
                    "currency_code": "EUR",
                    "value": total_eur,
                },
            }
        ],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
    }

    r = requests.post(
        f"{cfg.base_url}/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )
    r.raise_for_status()
    data: dict[str, Any] = r.json()
    return data


def _capture_paypal_order(paypal_order_id: str) -> dict[str, Any]:
    cfg = _paypal_config()
    token = _get_access_token()

    r = requests.post(
        f"{cfg.base_url}/v2/checkout/orders/{paypal_order_id}/capture",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=20,
    )
    r.raise_for_status()
    data: dict[str, Any] = r.json()
    return data


class PayPalProvider(PaymentProvider):
    slug = "paypal"

    def create_payment(
        self,
        *,
        order: Order,
        return_url: str,
        cancel_url: str,
    ) -> PaymentResult:
        data = _create_paypal_order(
            total_eur=str(order.subtotal),
            reference_id=str(order.id),
            return_url=return_url,
            cancel_url=cancel_url,
        )

        paypal_id = data["id"]

        redirect_url: str | None = None
        for link in data.get("links", []):
            if link.get("rel") == "approve":
                redirect_url = link["href"]
                break

        return PaymentResult(
            approved=True,
            provider_order_id=paypal_id,
            redirect_url=redirect_url,
        )

    def capture_payment(
        self,
        *,
        provider_order_id: str,
    ) -> CaptureResult:
        data = _capture_paypal_order(provider_order_id)

        capture_id = data["purchase_units"][0]["payments"]["captures"][0]["id"]

        return CaptureResult(
            approved=True,
            capture_id=capture_id,
        )
