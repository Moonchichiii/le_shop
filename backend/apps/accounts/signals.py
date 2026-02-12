from typing import Any

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomerProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender: Any, instance: Any, created: bool, **kwargs: Any) -> None:
    if created:
        CustomerProfile.objects.get_or_create(user=instance)
