from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from playwright.sync_api import Page, expect

from backend.apps.orders.models import Order
from backend.apps.orders.signing import sign_order_id  # correct import
from backend.tests.e2e.utils import create_product, create_verified_user

User = get_user_model()


@override_settings(
    ACCOUNT_LOGIN_METHODS={"username", "email"},
    ACCOUNT_EMAIL_VERIFICATION="none",  # skip email confirmation in tests
)
def test_cart_session_persistence_across_auth(page: Page, live_server):
    product = create_product()
    password = "password123"
    create_verified_user(email="merge@test.com", password=password, username="merger")

    # 1. Guest adds item
    page.goto(f"{live_server.url}{product.get_absolute_url()}")
    page.locator("button:has-text('Add to cart')").click()
    expect(page.get_by_test_id("cart-count")).to_have_text("1")

    # 2. Login with password (forced by override_settings)
    page.goto(f"{live_server.url}/accounts/login/")
    page.wait_for_selector("input[name='login']")
    page.fill("input[name='login']", "merge@test.com")
    page.fill('[data-testid="password"]', password)
    page.locator('form[action*="login"] button[type="submit"]').click()

    # 3. Force redirect to home (bypass confirmation)
    page.goto(f"{live_server.url}/")

    # 4. Cart should persist
    expect(page.get_by_test_id("cart-count")).to_have_text("1")

    # 5. Logout – click the account menu first
    page.locator('button[aria-label="Account"]').click()  # open account menu
    page.locator('button:has-text("Sign out")').click()

    # 6. Cart should be empty for next guest
    page.goto(f"{live_server.url}/")
    expect(page.get_by_test_id("cart-count")).to_be_hidden()


def test_security_order_isolation(page: Page, live_server):
    user_a = create_verified_user(email="a@test.com", password="p", username="usera")
    order_a = Order.objects.create(user=user_a, email="a@test.com", status="paid")
    token = sign_order_id(order_a.id)
    guest_link = f"{live_server.url}/order/receipt/{token}/"
    create_verified_user(email="b@test.com", password="p", username="userb")

    # Login as User B
    page.goto(f"{live_server.url}/accounts/login/")
    page.wait_for_selector("input[name='login']")
    page.fill("input[name='login']", "b@test.com")
    page.fill('[data-testid="password"]', "p")
    page.locator('form[action*="login"] button[type="submit"]').click()
    response = page.goto(guest_link)
    assert response.status == 404
