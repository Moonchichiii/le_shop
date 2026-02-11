from .base import *  # noqa: F401,F403
from .base import DATABASES  # noqa: F811

# Local development
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Email
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Static storage (no manifest hashing)
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Database (relax SSL for local)
DATABASES["default"]["OPTIONS"] = DATABASES["default"].get("OPTIONS", {})
DATABASES["default"]["OPTIONS"].pop("sslmode", None)
