from decimal import Decimal

from cloudinary.models import CloudinaryField  # type: ignore
from cloudinary.utils import cloudinary_url
from django.db import models
from django.urls import reverse


class Category(models.Model):
    name: models.CharField = models.CharField(max_length=100)
    slug: models.SlugField = models.SlugField(unique=True)
    description: models.TextField = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self) -> str:
        return str(self.name)


class Product(models.Model):
    category: models.ForeignKey = models.ForeignKey(
        Category, related_name="products", on_delete=models.CASCADE
    )
    name: models.CharField = models.CharField(max_length=200)
    slug: models.SlugField = models.SlugField(unique=True)

    image = CloudinaryField("image", folder="le_shop/products")

    # NEW: Mandatory Accessibility Field
    image_alt = models.CharField(
        max_length=200,
        help_text=(
            "Brief description of the image for screen readers "
            "(e.g., 'Blue ceramic vase on oak table')."
        ),
    )

    description: models.TextField = models.TextField()
    price: models.DecimalField = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    is_active: models.BooleanField = models.BooleanField(default=True)
    stock: models.PositiveIntegerField = models.PositiveIntegerField(default=0)

    is_featured: models.BooleanField = models.BooleanField(default=False)
    is_new: models.BooleanField = models.BooleanField(default=False)

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return str(self.name)

    def get_absolute_url(self) -> str:
        return reverse("product_detail", kwargs={"slug": self.slug})

    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0

    def image_url(self, *, width: int | None = None, height: int | None = None) -> str:
        if not self.image:
            return ""

        t: dict[str, object] = {
            "fetch_format": "auto",
            "quality": "auto",
        }

        if width and height:
            t.update(
                {"width": width, "height": height, "crop": "fill", "gravity": "auto"}
            )
        elif width:
            t.update({"width": width, "crop": "fill", "gravity": "auto"})
        elif height:
            t.update({"height": height, "crop": "fill", "gravity": "auto"})

        url, _ = cloudinary_url(self.image.public_id, transformation=t)
        return url

    @property
    def image_url_auto(self) -> str:
        return self.image_url()

    @property
    def image_url_200(self) -> str:
        return self.image_url(width=200)

    @property
    def image_url_400(self) -> str:
        return self.image_url(width=400)

    @property
    def image_url_800(self) -> str:
        return self.image_url(width=800)

    @property
    def image_url_1200(self) -> str:
        return self.image_url(width=1200)
