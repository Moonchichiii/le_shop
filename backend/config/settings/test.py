from .base import *  # noqa: F401,F403

# Test environment
DEBUG = False

# Fast password hashing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# In-memory email
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# In-memory file storage
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# In-memory database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
