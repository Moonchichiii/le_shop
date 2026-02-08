import os
from unittest.mock import MagicMock

import pytest
import requests

# Must be set before Django touches the DB in an async-detected context.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


def pytest_collection_modifyitems(items):
    """
    Auto-mark all tests inside backend/tests/e2e/ as @pytest.mark.e2e
    so you never repeat pytestmark in each file.
    """
    for item in items:
        path = str(item.fspath)
        if "backend/tests/e2e/" in path.replace("\\", "/"):
            item.add_marker(pytest.mark.e2e)


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
    Returns a relative 'approve' URL so Playwright stays on the live_server domain.
    """
    mock_post = MagicMock()

    def side_effect(url, *args, **kwargs):
        # 1) Access Token
        if "oauth2/token" in url:
            r = requests.Response()
            r.status_code = 200
            r.json = lambda: {"access_token": "FAKE_TOKEN_123"}
            return r

        # 2) Create Order
        if "checkout/orders" in url and "capture" not in url:
            r = requests.Response()
            r.status_code = 201
            r.json = lambda: {
                "id": "FAKE_PAYPAL_ORDER_ID",
                "links": [{"rel": "approve", "href": "/mock-paypal-approve"}],
            }
            return r

        # 3) Capture Order
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
