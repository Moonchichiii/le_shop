import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory

from backend.apps.cart.cart import Cart
from backend.apps.products.models import Category, Product


@pytest.fixture
def category():
    return Category.objects.create(name="Test Cat", slug="test-cat")


@pytest.fixture
def product(category):
    return Product.objects.create(
        category=category,
        name="Test Product",
        slug="test-product",
        price=100.00,
        stock=10,
        is_active=True,
    )


@pytest.fixture
def request_with_session():
    factory = RequestFactory()
    request = factory.get("/")
    middleware = SessionMiddleware(lambda x: HttpResponse("OK"))
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.fixture
def cart_with_item(request_with_session, product):
    """Returns a Cart instance pre-filled with 1 product."""
    cart = Cart(request_with_session)
    cart.add(product, quantity=1)
    return cart
