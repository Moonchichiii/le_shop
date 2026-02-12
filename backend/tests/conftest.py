import os
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


def pytest_collection_modifyitems(items):  # type: ignore[no-untyped-def]
    for item in items:
        path = str(item.fspath)
        if "backend/tests/e2e/" in path.replace("\\", "/"):
            item.add_marker(pytest.mark.e2e)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):  # type: ignore[no-untyped-def]
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "reduced_motion": "reduce",
    }


@pytest.fixture
def page(page):  # type: ignore[no-untyped-def]
    page.set_default_timeout(5000)
    return page


def _mock_response(status_code: int, json_data: dict) -> MagicMock:  # type: ignore[type-arg]
    """Build a mock that behaves like requests.Response."""
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_data
    r.ok = status_code < 400
    return r


@pytest.fixture(autouse=True)
def mock_paypal(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_post = MagicMock()

    def side_effect(url: str, *args: object, **kwargs: object) -> MagicMock:
        if "oauth2/token" in url:
            return _mock_response(200, {"access_token": "FAKE_TOKEN_123"})

        if "checkout/orders" in url and "capture" not in url:
            return _mock_response(
                201,
                {
                    "id": "FAKE_PAYPAL_ORDER_ID",
                    "links": [
                        {
                            "rel": "approve",
                            "href": "/mock-paypal-approve",
                        }
                    ],
                },
            )

        if "capture" in url:
            return _mock_response(
                201,
                {
                    "id": "FAKE_PAYPAL_ORDER_ID",
                    "status": "COMPLETED",
                    "purchase_units": [
                        {"payments": {"captures": [{"id": "FAKE_CAPTURE_ID"}]}}
                    ],
                },
            )

        return _mock_response(200, {})

    mock_post.side_effect = side_effect
    monkeypatch.setattr("requests.post", mock_post)
