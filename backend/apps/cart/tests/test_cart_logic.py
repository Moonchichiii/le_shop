import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory

from backend.apps.cart.services import Cart
from backend.apps.products.models import Category, Product


def get_request_with_session():
    factory = RequestFactory()
    request = factory.get("/")
    # FIX: Return a real HttpResponse object to satisfy mypy
    middleware = SessionMiddleware(lambda x: HttpResponse())
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.mark.django_db
class TestCartLogic:
    @pytest.fixture(autouse=True)
    def setup_category(self):
        """Automatically create a category for all tests in this class."""
        self.category = Category.objects.create(name="Test Cat", slug="test-cat")

    def create_product(self, name="Test Item", price=10.00, stock=100):
        return Product.objects.create(
            category=self.category,
            name=name,
            slug=name.lower().replace(" ", "-"),
            price=price,
            stock=stock,
        )

    def test_add_new_product(self):
        product = self.create_product()
        request = get_request_with_session()
        cart = Cart(request)

        result = cart.add(product, quantity=2)

        assert result.final == 2
        assert result.clamped is False
        assert len(cart) == 2
        assert cart.get_total_price() == 20.00

    def test_add_existing_product_accumulates(self):
        product = self.create_product()
        request = get_request_with_session()
        cart = Cart(request)

        cart.add(product, quantity=1)
        result = cart.add(product, quantity=2)

        assert result.final == 3
        assert len(cart) == 3

    def test_add_override_quantity(self):
        product = self.create_product()
        request = get_request_with_session()
        cart = Cart(request)

        cart.add(product, quantity=5)
        result = cart.add(product, quantity=2, override=True)

        assert result.final == 2
        assert len(cart) == 2

    def test_stock_limit_clamping(self):
        product = self.create_product(name="Rare Item", stock=5)
        request = get_request_with_session()
        cart = Cart(request)

        result = cart.add(product, quantity=10)

        assert result.final == 5
        assert result.clamped is True
        assert result.max_stock == 5
        assert len(cart) == 5

    def test_add_zero_stock_removes_item(self):
        product = self.create_product(name="Gone Item", stock=0)
        request = get_request_with_session()
        cart = Cart(request)

        result = cart.add(product, quantity=1)

        assert result.removed is True
        assert result.final == 0
        assert len(cart) == 0

    def test_remove_product(self):
        product = self.create_product(name="Item")
        request = get_request_with_session()
        cart = Cart(request)

        cart.add(product)
        assert len(cart) == 1

        cart.remove(product)
        assert len(cart) == 0

    def test_cart_iterator_syncs_with_db(self):
        p1 = self.create_product(name="P1")
        p2 = self.create_product(name="P2")

        request = get_request_with_session()
        cart = Cart(request)
        cart.add(p1)
        cart.add(p2)

        items = list(cart)
        assert len(items) == 2

        p2.is_active = False
        p2.save()

        items = list(cart)
        assert len(items) == 1
        assert items[0]["product"] == p1
