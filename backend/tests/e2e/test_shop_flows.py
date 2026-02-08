import os
import re

import pytest
from playwright.sync_api import Page, expect

from backend.apps.products.models import Category, Product

# --- CRITICAL: Allow Playwright to touch the DB ---
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Mark this entire file as requiring the DB and being an E2E test
pytestmark = [pytest.mark.django_db, pytest.mark.e2e]


def test_homepage_styling_and_accessibility(page: Page, live_server):
    """
    Verifies that the design system CSS is properly loaded and applied.
    """
    page.goto(f"{live_server.url}/")

    # 1. Check Page Title - use regex pattern instead of lambda
    expect(page).to_have_title(re.compile(r"Leptis|Shop", re.IGNORECASE))

    # 2. Verify CSS Variables are Applied
    # Check the body background color matches the design system
    body = page.locator("body")

    # Note: hex #fbf7f0 converts to rgb(251, 247, 240) in computed styles
    expect(body).to_have_css("background-color", "rgb(251, 247, 240)")

    # 3. Verify Button Styling
    # Check that primary buttons have the correct border-radius
    primary_button = page.locator(".btn-primary").first
    if primary_button.is_visible():
        expect(primary_button).to_have_css("border-radius", "0px")


def test_add_product_to_cart_interaction(page: Page, live_server):
    """
    Tests the complete user flow for adding a product to cart:
    1. Navigate to shop page
    2. Click add to cart button (HTMX request)
    3. Verify cart badge updates without page reload
    """
    # --- SETUP TEST DATA ---
    category = Category.objects.create(name="Lamps", slug="lamps")
    product = Product.objects.create(
        name="Designer Table Lamp",
        slug="designer-table-lamp",
        price=100.00,
        category=category,
        is_in_stock=True,
    )

    # --- NAVIGATE TO SHOP ---
    page.goto(f"{live_server.url}/shop/")

    # Locate the cart badge in the navigation header
    # Adjust selector based on your actual header structure
    cart_badge = page.locator("header a[aria-label='Cart']")

    # Locate the add to cart button for this specific product
    add_to_cart_button = page.locator(f"form[action*='{product.id}'] button")

    # Click the add to cart button
    add_to_cart_button.click()

    # --- VERIFY HTMX UPDATE ---
    # Cart badge should update to "1" without full page reload
    # This confirms HTMX successfully swapped the HTML fragment
    expect(cart_badge).to_contain_text("1", timeout=5000)

    # Verify we remain on the shop page (no full redirect occurred)
    expect(page).to_have_url(f"{live_server.url}/shop/")


def test_product_search_filtering(page: Page, live_server):
    """
    Tests that the search functionality filters products dynamically via HTMX.
    """
    category = Category.objects.create(name="Home Decor", slug="home-decor")
    product_one = Product.objects.create(
        name="Brass Decorative Vase", price=50, category=category
    )
    product_two = Product.objects.create(
        name="Chrome Serving Tray", price=50, category=category
    )

    page.goto(f"{live_server.url}/shop/")

    # Verify both products are initially visible
    expect(page.locator(f"text={product_one.name}")).to_be_visible()
    expect(page.locator(f"text={product_two.name}")).to_be_visible()

    # Enter search query
    page.fill("input[name='q']", "Brass")

    # Submit search form
    page.locator("button", has_text="Search").click()

    # Verify filtered results: only matching product should be visible
    expect(page.locator(f"text={product_two.name}")).not_to_be_visible()
    expect(page.locator(f"text={product_one.name}")).to_be_visible()
