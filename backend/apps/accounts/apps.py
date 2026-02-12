from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.accounts"

    def ready(self) -> None:
        from . import signals  # noqa: F401
