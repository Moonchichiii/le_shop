import os
import re
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page, expect

from backend.apps.orders.models import Order
from backend.apps.products.models import Category, Product

User = get_user_model()

# --- CONFIG ---
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
pytestmark = [pytest.mark.django_db, pytest.mark.e2e]


# --- HELPER ---
def create_product(name="Test Item", price=50, stock=5, slug="test-item"):
    cat, _ = Category.objects.get_or_create(name="Decor", slug="decor")
    return Product.objects.create(
        name=name,
        slug=slug,
        price=price,
        stock=stock,
        category=cat,
        is_active=True,
        image_alt="Test Image",
    )


def test_checkout_data_integrity_and_network_efficiency(page: Page, live_server):
    """
    AUDIT TEST: Verifies data integrity during the checkout process and ensures
    efficient network usage (no double-submissions).
    """
    # Intercept PayPal redirect to stay on localhost
    page.route(
        "**/*mock-paypal-approve*",
        lambda route: route.fulfill(
            status=200,
            body="<html><body><h1>PayPal Payment Page</h1></body></html>",
        ),
    )

    price = Decimal("150.00")
    product = create_product(price=price, stock=10)

    # Spy on network requests
    add_to_cart_requests = []
    page.on(
        "request",
        lambda request: (
            add_to_cart_requests.append(request) if "cart/add" in request.url else None
        ),
    )

    # Action: Add to Cart
    page.goto(f"{live_server.url}{product.get_absolute_url()}")
    page.locator("button:has-text('Add to cart')").click()

    page.wait_for_load_state("networkidle")
    assert len(add_to_cart_requests) == 1, (
        "Frontend triggered multiple add-to-cart requests for a single click!"
    )

    # Action: Checkout
    page.goto(f"{live_server.url}/cart/")

    # Verify Price UI
    total_ui = page.locator("p.headline-serif").text_content()
    assert "150" in total_ui

    page.locator("button:has-text('Proceed to Checkout')").click()

    # Action: Guest Details
    page.fill("input[name='email']", "audit@example.com")
    page.locator("button:has-text('Continue to payment')").click()

    # Verify we hit the mocked PayPal page
    expect(page.locator("h1")).to_contain_text("PayPal Payment Page")

    # DB Audit
    order = Order.objects.get(email="audit@example.com")
    assert order.status == "pending"
    assert order.subtotal == price
    assert order.items.count() == 1
    assert order.paypal_order_id == "FAKE_PAYPAL_ORDER_ID"

    # Action: Trigger Return Callback
    return_url = f"{live_server.url}/paypal/return/?token=FAKE_PAYPAL_ORDER_ID"
    page.goto(return_url)

    # Final DB Audit
    order.refresh_from_db()
    assert order.status == "paid"
    assert order.paypal_capture_id is not None
    product.refresh_from_db()
    assert product.stock == 9


def test_concurrency_sold_out_during_checkout(page: Page, live_server):
    """
    EDGE CASE: Simulates an item selling out while the user is typing their email.
    """
    product = create_product(stock=1)

    page.goto(f"{live_server.url}{product.get_absolute_url()}")
    page.locator("button:has-text('Add to cart')").click()

    page.goto(f"{live_server.url}/cart/")
    page.locator("button:has-text('Proceed to Checkout')").click()
    page.fill("input[name='email']", "slow@example.com")

    # Simulate: Backend stock drops to 0
    product.stock = 0
    product.save()

    page.locator("button:has-text('Continue to payment')").click()

    # Expect redirect back to cart with error message
    expect(page).to_have_url(re.compile(r".*/cart/"))
    expect(page.locator("body")).to_contain_text("no longer available")

    assert Order.objects.filter(email="slow@example.com").exists() is False


def test_smart_stock_ui_feedback(page: Page, live_server):
    """
    UX AUDIT: Verifies that requesting more than available stock is clamped
    by the server and feedback is shown to the user.
    """
    product = create_product(stock=2)

    page.goto(f"{live_server.url}{product.get_absolute_url()}")

    # FORCE: Remove 'max' attribute via JS to ensure backend logic is tested
    # regardless of browser validation.
    page.evaluate(
        "document.querySelector('input[name=\"qty\"]').removeAttribute('max')"
    )

    page.fill("input[name='qty']", "5")

    # Target specific button
    page.locator("input[name='qty']").locator("xpath=../../..").locator(
        "button"
    ).click()

    # Backend clamps 5 -> 2. Cart badge matches items/qty.
    expect(page.get_by_test_id("cart-count")).to_have_text("2")

    page.goto(f"{live_server.url}/cart/")
    expect(page.get_by_test_id("flash")).to_contain_text("Only 2 left")

    expect(page.get_by_test_id(f"cart-line-qty-{product.id}")).to_have_text("2")


def test_cart_session_persistence_across_auth(page: Page, live_server):
    """
    INTEGRITY AUDIT: Cart merging/persistence across login.
    """
    product = create_product()
    password = "password123"
    User.objects.create_user(
        username="merger", email="merge@test.com", password=password
    )

    # 1. Guest adds item
    page.goto(f"{live_server.url}{product.get_absolute_url()}")
    page.locator("button:has-text('Add to cart')").click()

    expect(page.get_by_test_id("cart-count")).to_have_text("1")

    # 2. Login
    page.goto(f"{live_server.url}/accounts/login/")

    # Wait for login form
    page.wait_for_selector("input[name='login']")

    page.fill("input[name='login']", "merge@test.com")

    # CRITICAL FIX: Use type='password' to avoid name mismatch/timeouts
    page.fill("input[type='password']", password)

    page.locator("button:has-text('Sign in')").click()

    # 3. Cart should persist
    expect(page.get_by_test_id("cart-count")).to_have_text("1")

    # 4. Logout
    page.goto(f"{live_server.url}/accounts/logout/")
    page.locator("button:has-text('Sign out')").click()

    # 5. Cart should be empty for next guest
    page.goto(f"{live_server.url}/")
    expect(page.get_by_test_id("cart-count")).to_be_hidden()


def test_security_order_isolation(page: Page, live_server):
    """
    SECURITY AUDIT: Users cannot see each other's orders via guessed links.
    """
    user_a = User.objects.create_user(
        username="usera", email="a@test.com", password="p"
    )
    order_a = Order.objects.create(user=user_a, email="a@test.com", status="paid")

    from backend.apps.orders.signing import sign_order_id

    token = sign_order_id(order_a.id)
    guest_link = f"{live_server.url}/order/receipt/{token}/"

    User.objects.create_user(username="userb", email="b@test.com", password="p")

    # Login as User B
    page.goto(f"{live_server.url}/accounts/login/")
    page.wait_for_selector("input[name='login']")

    page.fill("input[name='login']", "b@test.com")

    # CRITICAL FIX: Use type='password'
    page.fill("input[type='password']", "p")

    page.locator("button:has-text('Sign in')").click()

    # Attempt to access User A's link
    response = page.goto(guest_link)

    # Expect 404 (Not Found) or 403 (Forbidden)
    assert response.status == 404


def test_checkout_empty_cart_redirection(page: Page, live_server):
    """
    ROBUSTNESS AUDIT: Navigating to checkout with empty cart redirects properly.
    """
    page.goto(f"{live_server.url}/")

    expect(page.get_by_test_id("cart-count")).to_be_hidden()

    page.goto(f"{live_server.url}/checkout/")

    expect(page).to_have_url(re.compile(r".*/cart/"))

    expect(page.locator("body")).to_contain_text("cart is empty")


def test_mobile_menu_accessibility(page: Page, live_server):
    """
    A11Y AUDIT: Mobile menu logic + Keyboard support.
    """
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(f"{live_server.url}/")

    page.locator("button[aria-label='Open menu']").click()
    expect(page.locator("#mobile-menu")).to_be_visible()

    page.keyboard.press("Escape")

    expect(page.locator("#mobile-menu")).not_to_be_visible()


def test_search_performance_and_accuracy(page: Page, live_server):
    """
    PERFORMANCE AUDIT: Search functionality.
    """
    p1 = create_product(name="Golden Lamp", slug="gold-lamp")
    p2 = create_product(name="Silver Table", slug="silver-table")

    page.goto(f"{live_server.url}/")

    page.locator("header button[aria-label='Search']").click()

    page.fill("input[name='q']", "Golden")
    page.keyboard.press("Enter")

    expect(page).to_have_url(re.compile(r"q=Golden"))
    expect(page.locator(f"text={p1.name}")).to_be_visible()
    expect(page.locator(f"text={p2.name}")).not_to_be_visible()


def test_brutalist_css_variables(page: Page, live_server):
    """
    DESIGN SYSTEM: Ensure theme loaded.
    """
    page.goto(f"{live_server.url}/")
    body = page.locator("body")
    expect(body).to_have_css("background-color", "rgb(251, 247, 240)")
