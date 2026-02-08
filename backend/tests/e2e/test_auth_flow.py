from django.contrib.auth import get_user_model
from playwright.sync_api import Page, expect

from backend.apps.orders.models import Order
from backend.tests.e2e.utils import create_product, create_verified_user

User = get_user_model()


def test_cart_session_persistence_across_auth(page: Page, live_server):
    product = create_product()
    password = "password123"
    create_verified_user(email="merge@test.com", password=password, username="merger")

    # 1. Guest adds item
    page.goto(f"{live_server.url}{product.get_absolute_url()}")
    page.locator("button:has-text('Add to cart')").click()
    expect(page.get_by_test_id("cart-count")).to_have_text("1")

    # 2. Login
    page.goto(f"{live_server.url}/accounts/login/")
    page.wait_for_selector("input[name='login']")
    page.fill("input[name='login']", "merge@test.com")
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
    user_a = create_verified_user(email="a@test.com", password="p", username="usera")
    order_a = Order.objects.create(user=user_a, email="a@test.com", status="paid")

    from backend.apps.orders.signing import sign_order_id

    token = sign_order_id(order_a.id)
    guest_link = f"{live_server.url}/order/receipt/{token}/"

    create_verified_user(email="b@test.com", password="p", username="userb")

    # Login as User B
    page.goto(f"{live_server.url}/accounts/login/")
    page.wait_for_selector("input[name='login']")
    page.fill("input[name='login']", "b@test.com")
    page.fill("input[type='password']", "p")
    page.locator("button:has-text('Sign in')").click()

    response = page.goto(guest_link)
    assert response.status == 404
