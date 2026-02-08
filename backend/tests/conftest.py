import pytest


# This ensures Playwright tests run against the Django LiveServer
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
    }


@pytest.fixture
def page(page):
    """
    Overwrites the default page fixture to set a default timeout
    and base url if needed.
    """
    page.set_default_timeout(5000)
    return page
