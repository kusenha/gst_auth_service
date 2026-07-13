import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-this")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "apps.identity",
    "apps.rbac",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "auth_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "auth_service.wsgi.application"
ASGI_APPLICATION = "auth_service.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DB_NAME", "gst_auth_service"),
        "USER": os.getenv("DB_USER", "gst"),
        "PASSWORD": os.getenv("DB_PASSWORD", "S3cur3001"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

EDA_SOURCE_DB_NAME = os.getenv("EDA_SOURCE_DB_NAME", "")
if EDA_SOURCE_DB_NAME:
    DATABASES["eda_source"] = {
        "ENGINE": os.getenv("EDA_SOURCE_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": EDA_SOURCE_DB_NAME,
        "USER": os.getenv("EDA_SOURCE_DB_USER", "gst"),
        "PASSWORD": os.getenv("EDA_SOURCE_DB_PASSWORD", "S3cur3001"),
        "HOST": os.getenv("EDA_SOURCE_DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("EDA_SOURCE_DB_PORT", "5432"),
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Dar_es_Salaam"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Auth Service API",
    "VERSION": "1.0.0",
}

JWT_ACCESS_MINUTES = int(os.getenv("JWT_ACCESS_MINUTES", "60"))
JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "7"))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256").upper()
JWT_PRIVATE_KEY = os.getenv("JWT_PRIVATE_KEY", "")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "")
JWT_SHARED_SECRET = os.getenv("JWT_SHARED_SECRET", SECRET_KEY)

if JWT_ALGORITHM.startswith("RS") and (
    not JWT_PRIVATE_KEY
    or "..." in JWT_PRIVATE_KEY
    or not JWT_PUBLIC_KEY
    or "..." in JWT_PUBLIC_KEY
):
    # Fall back to symmetric tokens for local development when RSA keys are not configured.
    JWT_ALGORITHM = "HS256"
    JWT_PRIVATE_KEY = JWT_SHARED_SECRET
    JWT_PUBLIC_KEY = ""

if JWT_ALGORITHM == "HS256":
    JWT_PRIVATE_KEY = JWT_SHARED_SECRET
    JWT_PUBLIC_KEY = ""

SIMPLE_JWT = {
    "ALGORITHM": JWT_ALGORITHM,
    "SIGNING_KEY": JWT_PRIVATE_KEY,
    "VERIFYING_KEY": JWT_PUBLIC_KEY,
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=JWT_ACCESS_MINUTES),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=JWT_REFRESH_DAYS),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", True)

if not CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOWED_ORIGINS = env_list(
        "CORS_ALLOWED_ORIGINS",
        [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
    )

CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", True)

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

AUTH_INTERNAL_TOKEN = os.getenv("AUTH_INTERNAL_TOKEN", "")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000/api/notifications/events/")
NOTIFICATION_SERVICE_TIMEOUT_SECONDS = int(os.getenv("NOTIFICATION_SERVICE_TIMEOUT_SECONDS", "10"))
NOTIFICATION_SERVICE_QUEUE_MODE = env_bool("NOTIFICATION_SERVICE_QUEUE_MODE", True)
NOTIFICATION_INTERNAL_TOKEN = os.getenv("NOTIFICATION_INTERNAL_TOKEN", AUTH_INTERNAL_TOKEN)
