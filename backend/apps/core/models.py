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

        return self.image.build_url(
            width=1200,
            height=1500,
            crop="fill",
            quality="auto",
            format="auto",
            gravity="auto",
        )
