import re
from decimal import Decimal

from playwright.sync_api import Page, expect

from backend.apps.orders.models import Order
from backend.tests.e2e.utils import create_product


def test_checkout_data_integrity_and_network_efficiency(page: Page, live_server):
    page.route(
        "**/*mock-paypal-approve*",
        lambda route: route.fulfill(
            status=200,
            body="<html><body><h1>PayPal Payment Page</h1></body></html>",
        ),
    )

    price = Decimal("150.00")
    product = create_product(price=price, stock=10)

    add_to_cart_requests = []
    page.on(
        "request",
        lambda request: add_to_cart_requests.append(request)
        if "cart/add" in request.url
        else None,
    )

    page.goto(f"{live_server.url}{product.get_absolute_url()}")
    page.locator("button:has-text('Add to cart')").click()

    page.wait_for_load_state("networkidle")
    assert len(add_to_cart_requests) == 1

    page.goto(f"{live_server.url}/cart/")
    total_ui = page.locator("p.headline-serif").text_content()
    assert "150" in total_ui

    page.locator("button:has-text('Proceed to Checkout')").click()

    page.fill("input[name='email']", "audit@example.com")
    page.locator("button:has-text('Continue to payment')").click()

    expect(page.locator("h1")).to_contain_text("PayPal Payment Page")

    order = Order.objects.get(email="audit@example.com")
    assert order.status == "pending"
    assert order.subtotal == price
    assert order.items.count() == 1
    assert order.paypal_order_id == "FAKE_PAYPAL_ORDER_ID"

    return_url = f"{live_server.url}/paypal/return/?token=FAKE_PAYPAL_ORDER_ID"
    page.goto(return_url)

    order.refresh_from_db()
    assert order.status == "paid"
    assert order.paypal_capture_id is not None
    product.refresh_from_db()
    assert product.stock == 9


def test_concurrency_sold_out_during_checkout(page: Page, live_server):
    product = create_product(stock=1)

    page.goto(f"{live_server.url}{product.get_absolute_url()}")
    page.locator("button:has-text('Add to cart')").click()

    page.goto(f"{live_server.url}/cart/")
    page.locator("button:has-text('Proceed to Checkout')").click()
    page.fill("input[name='email']", "slow@example.com")

    product.stock = 0
    product.save()

    page.locator("button:has-text('Continue to payment')").click()

    expect(page).to_have_url(re.compile(r".*/cart/"))
    expect(page.locator("body")).to_contain_text("no longer available")
    assert Order.objects.filter(email="slow@example.com").exists() is False


def test_smart_stock_ui_feedback(page: Page, live_server):
    product = create_product(stock=2)

    page.goto(f"{live_server.url}{product.get_absolute_url()}")
    page.evaluate(
        "document.querySelector('input[name=\"qty\"]').removeAttribute('max')"
    )
    page.fill("input[name='qty']", "5")

    page.locator("input[name='qty']").locator("xpath=../../..").locator(
        "button"
    ).click()

    expect(page.get_by_test_id("cart-count")).to_have_text("2")

    page.goto(f"{live_server.url}/cart/")
    expect(page.get_by_test_id("flash")).to_contain_text("Only 2 left")
    expect(page.get_by_test_id(f"cart-line-qty-{product.id}")).to_have_text("2")


def test_checkout_empty_cart_redirection(page: Page, live_server):
    page.goto(f"{live_server.url}/")
    expect(page.get_by_test_id("cart-count")).to_be_hidden()

    page.goto(f"{live_server.url}/checkout/")
    expect(page).to_have_url(re.compile(r".*/cart/"))
    expect(page.locator("body")).to_contain_text("cart is empty")
