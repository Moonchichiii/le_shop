from .base import *  # noqa: F401,F403

# Production
DEBUG = False

# HTTPS / HSTS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Trusted origins
CSRF_TRUSTED_ORIGINS = [
    "https://your-app.onrender.com",
]

# Database — enforce SSL in production
DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

# Static files — cache-busting manifests
STORAGES = {
    "staticfiles": {
        "BACKEND": ("whitenoise.storage.CompressedManifestStaticFilesStorage"),
    },
}

# Email — swap to a real backend in production
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = config("EMAIL_HOST")
# EMAIL_PORT = config("EMAIL_PORT", cast=int, default=587)
# EMAIL_HOST_USER = config("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
# EMAIL_USE_TLS = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
