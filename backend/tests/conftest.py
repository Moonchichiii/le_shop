from unittest.mock import MagicMock

import pytest
import requests


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "reduced_motion": "reduce",
    }


@pytest.fixture
def page(page):
    page.set_default_timeout(5000)
    return page


@pytest.fixture(autouse=True)
def mock_paypal(monkeypatch):
    """
    Mocks PayPal API calls.
    Crucial Fix: Returns a relative URL for 'approve' link so the browser stays
    on the test server domain, avoiding DNS errors.
    """
    mock_post = MagicMock()

    def side_effect(url, *args, **kwargs):
        # 1. Access Token
        if "oauth2/token" in url:
            r = requests.Response()
            r.status_code = 200
            r.json = lambda: {"access_token": "FAKE_TOKEN_123"}
            return r

        # 2. Create Order
        if "checkout/orders" in url and "capture" not in url:
            r = requests.Response()
            r.status_code = 201
            r.json = lambda: {
                "id": "FAKE_PAYPAL_ORDER_ID",
                "links": [
                    # FIX: Use relative path. Playwright/Django will treat this
                    # as relative to the live_server root (e.g. localhost:port/mock...)
                    {
                        "rel": "approve",
                        "href": "/mock-paypal-approve",
                    }
                ],
            }
            return r

        # 3. Capture Order
        if "capture" in url:
            r = requests.Response()
            r.status_code = 201
            r.json = lambda: {
                "id": "FAKE_PAYPAL_ORDER_ID",
                "status": "COMPLETED",
                "purchase_units": [
                    {"payments": {"captures": [{"id": "FAKE_CAPTURE_ID"}]}}
                ],
            }
            return r

        return requests.Response()

    mock_post.side_effect = side_effect
    monkeypatch.setattr("requests.post", mock_post)
