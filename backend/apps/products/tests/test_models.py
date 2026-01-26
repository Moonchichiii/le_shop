from unittest.mock import Mock, patch

import pytest

from backend.apps.products.models import Category, Product


@pytest.mark.django_db
class TestProductModels:
    def test_category_str(self):
        cat = Category.objects.create(name="Tools", slug="tools")
        assert str(cat) == "Tools"

    def test_product_str(self):
        cat = Category.objects.create(name="Tools", slug="tools")
        prod = Product.objects.create(
            category=cat, name="Hammer", slug="hammer", price=10
        )
        assert str(prod) == "Hammer"

    # ... inside test_get_absolute_url ...
    def test_get_absolute_url(self):
        cat = Category.objects.create(name="Tools", slug="tools")
        prod = Product.objects.create(
            category=cat, name="Hammer", slug="hammer", price=10
        )
        # UPDATED: Changed from /products/hammer/ to /shop/hammer/
        assert prod.get_absolute_url() == "/shop/hammer/"

    def test_is_in_stock(self):
        cat = Category.objects.create(name="Tools", slug="tools")
        p1 = Product.objects.create(category=cat, name="In Stock", slug="p1", stock=5)
        p2 = Product.objects.create(category=cat, name="OOS", slug="p2", stock=0)

        assert p1.is_in_stock is True
        assert p2.is_in_stock is False

    @patch("backend.apps.products.models.cloudinary_url")
    def test_image_url_generation(self, mock_cloudinary_url):
        """
        Test that image helpers call the underlying library with correct params.
        """
        # Setup mock return value for cloudinary_url (url, options)
        mock_cloudinary_url.return_value = (
            "https://res.cloudinary.com/demo/image/upload/v1/sample.jpg",
            {},
        )

        cat = Category.objects.create(name="Test", slug="test")
        product = Product.objects.create(category=cat, name="P1", slug="p1")

        # Mock the image field on the instance
        product.image = Mock()
        product.image.public_id = "sample_id"

        # Test specific width (used in image_url_200)
        url = product.image_url_200

        assert url == "https://res.cloudinary.com/demo/image/upload/v1/sample.jpg"

        # Verify call arguments
        mock_cloudinary_url.assert_called_with(
            "sample_id",
            transformation={
                "fetch_format": "auto",
                "quality": "auto",
                "width": 200,
                "crop": "fill",
                "gravity": "auto",
            },
        )

    def test_image_url_no_image(self):
        """Ensure safe failure if no image is uploaded."""
        cat = Category.objects.create(name="Test", slug="test")
        product = Product.objects.create(category=cat, name="P1", slug="p1")
        # product.image is None/Empty by default here

        assert product.image_url() == ""
