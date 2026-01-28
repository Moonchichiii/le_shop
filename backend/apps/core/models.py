import cloudinary.utils
from cloudinary.models import CloudinaryField
from django.db import models


class HeroSlide(models.Model):
    title = models.CharField(
        max_length=100,
        help_text="The text that appears in the badge (e.g., 'Handcrafted')",
    )
    image = CloudinaryField("image")
    order = models.PositiveIntegerField(
        default=0, help_text="Lower numbers appear first"
    )
    is_active = models.BooleanField(default=True)
    alt_text = models.CharField(max_length=200, default="Artisan Object")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.title} (Order: {self.order})"

    @property
    def image_url(self):
        """
        Returns the Cloudinary URL with optimizations applied:
        - f_auto: Automatically serves WebP/AVIF if browser supports it
        - q_auto: Automatic quality compression (reduces 1.5MB -> ~50KB)
        - w_1200: Resizes to max width 1200px (retina ready but not huge)
        - c_fill: Crops to fill dimensions if needed
        """
        if not self.image:
            return ""

        url, options = cloudinary.utils.cloudinary_url(
            self.image.public_id,
            format="auto",
            quality="auto",
            width=1200,
            height=1500,
            crop="fill",
            gravity="auto",
            secure=True,
        )
        return url


class PageSection(models.Model):
    SECTION_CHOICES = (
        ("history", "History Section (Top)"),
        ("craft", "Craft Section (Bottom)"),
    )

    section_type = models.CharField(
        max_length=50,
        choices=SECTION_CHOICES,
        unique=True,
        help_text="Which part of the page is this for?",
    )
    image = CloudinaryField("image")

    def __str__(self):
        return self.get_section_type_display()

    # Optional helper (can be kept for future use)
    def get_optimized_url(self, width, height):
        if not self.image:
            return ""
        url, options = cloudinary.utils.cloudinary_url(
            self.image.public_id,
            format="auto",
            quality="auto",
            width=width,
            height=height,
            crop="fill",
            gravity="auto",
            secure=True,
        )
        return url

    @property
    def history_url(self):
        """Landscape 4:3 ratio for the History/Top section"""
        if not self.image:
            return ""
        url, options = cloudinary.utils.cloudinary_url(
            self.image.public_id,
            format="auto",
            quality="auto",
            width=1200,
            height=900,
            crop="fill",
            secure=True,
        )
        return url

    @property
    def craft_url(self):
        """Square 1:1 ratio for the Craft/Bottom section"""
        if not self.image:
            return ""
        url, options = cloudinary.utils.cloudinary_url(
            self.image.public_id,
            format="auto",
            quality="auto",
            width=1200,
            height=1200,
            crop="fill",
            secure=True,
        )
        return url
