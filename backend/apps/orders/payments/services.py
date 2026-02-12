from typing import cast

from django.conf import settings
from django.utils.module_loading import import_string

from .base import PaymentProvider


def get_payment_provider() -> PaymentProvider:
    provider = import_string(settings.PAYMENT_PROVIDER)()
    return cast(PaymentProvider, provider)
