import pytest
from django.urls import reverse

from backend.apps.products.models import Category, Product


@pytest.mark.django_db
class TestProductViews:
    @pytest.fixture
    def setup_catalog(self):
        cat1 = Category.objects.create(name="Electronics", slug="electronics")
        cat2 = Category.objects.create(name="Books", slug="books")

        p1 = Product.objects.create(
            category=cat1, name="Laptop", slug="laptop", price=1000, is_active=True
        )
        p2 = Product.objects.create(
            category=cat1, name="Old Phone", slug="old-phone", price=50, is_active=False
        )
        p3 = Product.objects.create(
            category=cat2,
            name="Django Guide",
            slug="django-guide",
            price=30,
            is_active=True,
            description="Learn python web",
        )
        return locals()  # returns dict of created objects

    def test_product_list_all_active(self, client, setup_catalog):
        """Test listing products ignores inactive ones."""
        url = reverse("products:product_list")
        response = client.get(url)

        assert response.status_code == 200
        page = response.context["page_obj"]
        products = response.context["products"]

        assert page.paginator.count == 2
        # 'Old Phone' is inactive, shouldn't be here
        assert setup_catalog["p1"] in products
        assert setup_catalog["p3"] in products
        assert setup_catalog["p2"] not in products

    def test_product_list_category_filter(self, client, setup_catalog):
        """Test filtering by category slug."""
        url = reverse("products:product_list")

        # Filter for Electronics
        response = client.get(url, {"category": "electronics"})
        page = response.context["page_obj"]
        products = response.context["products"]

        assert page.paginator.count == 1
        assert products[0] == setup_catalog["p1"]

    def test_product_list_search(self, client, setup_catalog):
        """Test searching by name or description."""
        url = reverse("products:product_list")

        # Search for "python" (in p3 description)
        response = client.get(url, {"q": "python"})
        page = response.context["page_obj"]
        products = response.context["products"]

        assert page.paginator.count == 1
        assert products[0] == setup_catalog["p3"]

        # Search for "Laptop" (in p1 name)
        response = client.get(url, {"q": "Laptop"})
        page = response.context["page_obj"]
        products = response.context["products"]
        assert products[0] == setup_catalog["p1"]

    def test_product_detail_success(self, client, setup_catalog):
        """Test viewing an active product detail."""
        p1 = setup_catalog["p1"]
        url = reverse("products:product_detail", args=[p1.slug])

        response = client.get(url)
        assert response.status_code == 200
        assert response.context["product"] == p1

    def test_product_detail_404_inactive(self, client, setup_catalog):
        """Test that inactive products return 404, not 200."""
        p2 = setup_catalog["p2"]  # Inactive
        url = reverse("products:product_detail", args=[p2.slug])

        response = client.get(url)
        assert response.status_code == 404

    def test_product_detail_404_nonexistent(self, client):
        url = reverse("products:product_detail", args=["ghost-product"])
        response = client.get(url)
        assert response.status_code == 404
