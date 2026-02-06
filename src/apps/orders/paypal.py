from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings


@dataclass(frozen=True)
class PayPalConfig:
    base_url: str
    client_id: str
    client_secret: str


def _paypal_config() -> PayPalConfig:
    env = (settings.PAYPAL_ENV or "sandbox").lower()
    base_url = (
        "https://api-m.sandbox.paypal.com"
        if env == "sandbox"
        else "https://api-m.paypal.com"
    )
    return PayPalConfig(
        base_url=base_url,
        client_id=settings.PAYPAL_CLIENT_ID,
        client_secret=settings.PAYPAL_CLIENT_SECRET,
    )


def get_access_token() -> str:
    cfg = _paypal_config()
    r = requests.post(
        f"{cfg.base_url}/v1/oauth2/token",
        auth=(cfg.client_id, cfg.client_secret),
        data={"grant_type": "client_credentials"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def create_order(
    *, total_eur: str, reference_id: str, return_url: str, cancel_url: str
) -> dict[str, Any]:
    """
    Creates a PayPal order and returns the JSON payload (contains id + links[]).
    """
    cfg = _paypal_config()
    token = get_access_token()

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
    return r.json()


def capture_order(paypal_order_id: str) -> dict[str, Any]:
    cfg = _paypal_config()
    token = get_access_token()

    r = requests.post(
        f"{cfg.base_url}/v2/checkout/orders/{paypal_order_id}/capture",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()
