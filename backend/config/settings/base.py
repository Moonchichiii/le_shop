from pathlib import Path

import cloudinary
import dj_database_url
from decouple import Csv, config

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Core
SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-key")
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
    cast=Csv(),
)

# Applications
INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django_htmx",
    "rest_framework",
    "django_filters",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
    "cloudinary",
    "cloudinary_storage",
    "csp",
    "backend.apps.accounts",
    "backend.apps.core",
    "backend.apps.products",
    "backend.apps.cart",
    "backend.apps.orders",
    "backend.apps.payments",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

# Internationalization
LANGUAGE_CODE = "en"
USE_I18N = True
LANGUAGES = [
    ("en", "English"),
    ("fr", "Français"),
]

# URLs / Templates
ROOT_URLCONF = "backend.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "backend" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "backend.apps.cart.context_processors.cart",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.config.wsgi.application"

# Database
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# Authentication & Allauth
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_USER_MODEL = "accounts.User"

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "first_name",
    "last_name",
]

ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_SESSION_REMEMBER = True

LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"
ACCOUNT_LOGOUT_REDIRECT_URL = "core:home"

ACCOUNT_FORMS = {
    "login": "backend.apps.core.forms.StyledLoginForm",
    "signup": "backend.apps.core.forms.StyledSignupForm",
}

ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/5m",
    "login": "20/5m",
    "signup": "10/1h",
}

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
    "facebook": {
        "METHOD": "oauth2",
        "SCOPE": ["email", "public_profile"],
        "FIELDS": [
            "id",
            "email",
            "name",
            "first_name",
            "last_name",
            "verified",
            "locale",
            "timezone",
            "link",
            "gender",
            "updated_time",
        ],
        "EXCHANGE_TOKEN": True,
        "VERIFIED_EMAIL": False,
        "VERSION": "v17.0",
    },
}

# Cookie defaults
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Email
DEFAULT_FROM_EMAIL = "Arti Corner <no-reply@articorner.local>"

# Security
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "https://cdn.jsdelivr.net",
            "https://unpkg.com",
            "https://cdnjs.cloudflare.com",
            "'unsafe-inline'",
            "'unsafe-eval'",
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
        ],
        "img-src": [
            "'self'",
            "data:",
            "https://res.cloudinary.com",
            "https://images.unsplash.com",
            "https://www.transparenttextures.com",
        ],
        "font-src": ["'self'", "data:"],
    }
}

# Cloudinary / Media
CLOUDINARY_CLOUD_NAME = config("CLOUDINARY_CLOUD_NAME", default="").strip()
CLOUDINARY_API_KEY = config("CLOUDINARY_API_KEY", default="").strip()
CLOUDINARY_API_SECRET = config("CLOUDINARY_API_SECRET", default="").strip()

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True,
)

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
    "API_KEY": CLOUDINARY_API_KEY,
    "API_SECRET": CLOUDINARY_API_SECRET,
    "MAGIC_FILE_PATH": "magic",
    "PREFIX": "arti_corner/",
}

# Payments
PAYMENT_PROVIDER = "backend.apps.orders.payments.providers.paypal.PayPalProvider"

PAYPAL_ENV = config("PAYPAL_ENV", default="sandbox")
PAYPAL_CLIENT_ID = config("PAYPAL_CLIENT_ID", default="")
PAYPAL_CLIENT_SECRET = config("PAYPAL_CLIENT_SECRET", default="")
PAYPAL_WEBHOOK_ID = config("PAYPAL_WEBHOOK_ID", default="")

# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "backend" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Django defaults
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Unfold admin theme
from .unfold import *  # noqa: E402,F401,F403
