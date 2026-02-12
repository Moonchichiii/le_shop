from .base import *  # noqa: F401,F403
from .base import BASE_DIR, DATABASES  # noqa: F811

# Local development
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "le-shop.onrender.com"]

# Email (file-based so links are clickable and not weirdly encoded)
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = BASE_DIR / "tmp" / "emails"

# Static storage (no manifest hashing)
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Database (relax SSL for local)
DATABASES["default"]["OPTIONS"] = DATABASES["default"].get("OPTIONS", {})
DATABASES["default"]["OPTIONS"].pop("sslmode", None)
