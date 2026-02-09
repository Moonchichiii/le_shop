from decimal import Decimal

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

from backend.apps.products.models import Category, Product

User = get_user_model()


def create_verified_user(
    email="merge@test.com", password="password123", username="merger"
):
    user = User.objects.create_user(username=username, email=email, password=password)
    EmailAddress.objects.create(user=user, email=email, primary=True, verified=True)
    return user


def create_product(name="Test Item", price=Decimal("50.00"), stock=5, slug="test-item"):
    cat, _ = Category.objects.get_or_create(name="Decor", slug="decor")
    product = Product.objects.create(
        name=name,
        slug=slug,
        price=price,
        stock=stock,
        category=cat,
        is_active=True,
        image_alt="Test Image",
        image="le_shop/placeholder",
    )
    return product
