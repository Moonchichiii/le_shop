import re

import pytest
from django.conf import settings
from django.core import mail
from django.test.utils import override_settings
from playwright.sync_api import Page, expect

from backend.apps.orders.models import Order
from backend.apps.orders.signing import sign_order_id
from backend.tests.e2e.utils import create_product, create_verified_user

settings.ALLOWED_HOSTS.append("testserver")


def _extract_login_code_from_outbox() -> str:
    """
    Extract the login code from the latest allauth email.

    This is intentionally flexible: it searches subject+body for a
    6-character alphanumeric code (allauth may use letters and digits).
    Adjust regex if your allauth code length differs.
    """
    assert mail.outbox, "No email was sent (mail.outbox is empty)."

    msg = mail.outbox[-1]
    haystack = f"{msg.subject}\n{msg.body}"

    m = re.search(r"\b([A-Za-z0-9]{6})\b", haystack)
    assert m, f"Could not find a 6-character login code in email:\n\n{haystack}"
    return m.group(1)


@pytest.mark.django_db
@override_settings(
    ACCOUNT_LOGIN_METHODS={"email"},
    ACCOUNT_EMAIL_VERIFICATION="none",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_cart_session_persistence_across_auth(page: Page, live_server):
    product = create_product()
    create_verified_user(email="merge@test.com", password=None, username="merger")

    # 1) Guest adds item
    page.goto(f"{live_server.url}{product.get_absolute_url()}")
    page.locator("button:has-text('Add to cart')").click()
    expect(page.get_by_test_id("cart-count")).to_have_text("1")

    # 2) Start passwordless login
    page.goto(f"{live_server.url}/accounts/login/")
    page.wait_for_selector("input[name='login']")
    page.fill("input[name='login']", "merge@test.com")
    page.locator("form button[type='submit']").click()

    # 3) Allauth should redirect to code-confirm screen
    page.wait_for_url("**/accounts/login/code/confirm/**")

    # 4) Pull code from locmem outbox + confirm
    code = _extract_login_code_from_outbox()
    page.wait_for_selector("input[name='code']")
    page.fill("input[name='code']", code)
    page.get_by_role("button", name="Confirm").click()

    # 5) Now logged in, cart should still be there
    page.goto(f"{live_server.url}/")
    expect(page.get_by_test_id("cart-count")).to_have_text("1")

    # 6) Logout (your UI-driven flow)
    page.locator('button[aria-label="Account"]').click()
    page.locator('button:has-text("Sign out")').click()

    # 7) Back home as guest - cart badge should be hidden/empty
    page.goto(f"{live_server.url}/")
    expect(page.get_by_test_id("cart-count")).to_be_hidden()


@pytest.mark.django_db
@override_settings(
    ACCOUNT_EMAIL_VERIFICATION="none",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_security_order_isolation(page: Page, live_server):
    user_a = create_verified_user(email="a@test.com", password=None, username="usera")
    order_a = Order.objects.create(user=user_a, email="a@test.com", status="paid")

    token = sign_order_id(order_a.id)
    # Correct route: /orders/order/receipt/
    guest_link = f"{live_server.url}/orders/order/receipt/{token}/"

    create_verified_user(email="b@test.com", password=None, username="userb")

    # Login as user B (passwordless)
    page.goto(f"{live_server.url}/accounts/login/")
    page.wait_for_selector("input[name='login']")
    page.fill("input[name='login']", "b@test.com")
    page.locator("form button[type='submit']").click()

    page.wait_for_url("**/accounts/login/code/confirm/**")

    code = _extract_login_code_from_outbox()
    page.wait_for_selector("input[name='code']")
    page.fill("input[name='code']", code)
    page.get_by_role("button", name="Confirm").click()

    # User B should not access User A receipt
    response = page.goto(guest_link)
    assert response.status == 404
