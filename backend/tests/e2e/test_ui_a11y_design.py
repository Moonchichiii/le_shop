import re

from playwright.sync_api import Page, expect

from backend.tests.e2e.utils import create_product


def test_mobile_menu_accessibility(page: Page, live_server):
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(f"{live_server.url}/")

    page.locator("button[aria-label='Open menu']").click()
    expect(page.locator("#mobile-menu")).to_be_visible()

    page.keyboard.press("Escape")
    expect(page.locator("#mobile-menu")).not_to_be_visible()


def test_search_performance_and_accuracy(page: Page, live_server):
    p1 = create_product(name="Golden Lamp", slug="gold-lamp")
    p2 = create_product(name="Silver Table", slug="silver-table")

    page.goto(f"{live_server.url}/shop/?q=Golden")

    expect(page).to_have_url(re.compile(r"q=Golden"))

    expect(page.locator(f"a[href$='/{p1.slug}/']")).to_be_visible()
    expect(page.locator(f"a[href$='/{p2.slug}/']")).to_have_count(0)
