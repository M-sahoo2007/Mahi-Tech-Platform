import os
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

debug_value = os.getenv("DJANGO_DEBUG", "False").strip().lower()
if debug_value not in {"true", "false"}:
    raise ImproperlyConfigured("DJANGO_DEBUG must be either true or false.")
DEBUG = debug_value == "true"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "").strip()
if not SECRET_KEY and DEBUG:
    SECRET_KEY = "dev-only-change-me"
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required.")
if not DEBUG and (len(SECRET_KEY) < 50 or "replace-" in SECRET_KEY.lower()):
    raise ImproperlyConfigured("Production DJANGO_SECRET_KEY must be a non-placeholder value of at least 50 characters.")

ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]
if not DEBUG and (not os.getenv("DJANGO_ALLOWED_HOSTS", "").strip() or "*" in ALLOWED_HOSTS):
    raise ImproperlyConfigured("Production DJANGO_ALLOWED_HOSTS must be explicitly configured without wildcards.")

cache_url = os.getenv("CACHE_URL", "").strip()
if cache_url:
    parsed_cache_url = urlsplit(cache_url)
    if parsed_cache_url.scheme not in {"redis", "rediss"} or not parsed_cache_url.hostname:
        raise ImproperlyConfigured("CACHE_URL must be a valid redis:// or rediss:// URL.")
    if not DEBUG and parsed_cache_url.scheme != "rediss":
        raise ImproperlyConfigured("Production CACHE_URL must use rediss:// TLS.")
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": cache_url,
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
elif DEBUG:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "mahi-tech-development-cache",
        }
    }
else:
    raise ImproperlyConfigured("Production requires CACHE_URL for shared login throttling.")

try:
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "5"))
    LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "900"))
except ValueError as error:
    raise ImproperlyConfigured("Login rate-limit values must be positive integers.") from error
if LOGIN_RATE_LIMIT_MAX_ATTEMPTS < 1 or LOGIN_RATE_LIMIT_WINDOW_SECONDS < 1:
    raise ImproperlyConfigured("Login rate-limit values must be positive integers.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "accounts.apps.AccountsConfig",
    "clients.apps.ClientsConfig",
    "crm.apps.CrmConfig",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

postgres_variables = ("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST")
database_engine = os.getenv("DB_ENGINE", "").strip().lower()
postgres_values_present = any(os.getenv(name, "").strip() for name in postgres_variables)

if not database_engine:
    if postgres_values_present:
        database_engine = "postgresql"
    elif DEBUG:
        database_engine = "sqlite"
    else:
        raise ImproperlyConfigured("Production requires DB_ENGINE=postgresql and complete database settings.")

if database_engine == "sqlite":
    if not DEBUG:
        raise ImproperlyConfigured("SQLite is available only when DJANGO_DEBUG=true.")
    sqlite_name = os.getenv("SQLITE_DB_NAME", "dev.sqlite3").strip()
    sqlite_filename = Path(sqlite_name)
    if not sqlite_name or sqlite_filename.name != sqlite_name or sqlite_filename.suffix != ".sqlite3":
        raise ImproperlyConfigured("SQLITE_DB_NAME must be a local .sqlite3 filename without path components.")
    sqlite_path = (BASE_DIR / sqlite_filename).resolve()
    if sqlite_path == (BASE_DIR / "db.sqlite3").resolve():
        raise ImproperlyConfigured("The legacy db.sqlite3 file is protected and cannot be selected.")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_path,
        }
    }
elif database_engine in {"postgres", "postgresql"}:
    missing_database_variables = [name for name in postgres_variables if not os.getenv(name, "").strip()]
    if missing_database_variables:
        missing_names = ", ".join(missing_database_variables)
        raise ImproperlyConfigured(f"PostgreSQL requires these settings: {missing_names}.")

    database_port_value = os.getenv("DB_PORT", "5432").strip()
    try:
        database_port = int(database_port_value)
    except ValueError as error:
        raise ImproperlyConfigured("DB_PORT must be an integer between 1 and 65535.") from error
    if not 1 <= database_port <= 65535:
        raise ImproperlyConfigured("DB_PORT must be an integer between 1 and 65535.")

    sslmode = os.getenv("DB_SSLMODE", "require").strip().lower()
    allowed_ssl_modes = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
    if sslmode not in allowed_ssl_modes:
        raise ImproperlyConfigured("DB_SSLMODE must be a supported PostgreSQL SSL mode.")
    if not DEBUG and sslmode not in {"require", "verify-ca", "verify-full"}:
        raise ImproperlyConfigured("Production PostgreSQL connections must require TLS.")

    if not DEBUG:
        placeholder_markers = ("replace-", "your-", "example", "placeholder")
        for name in postgres_variables:
            value = os.getenv(name, "").strip().lower()
            if any(marker in value for marker in placeholder_markers):
                raise ImproperlyConfigured(f"Production {name} must not contain a placeholder value.")

    try:
        connection_max_age = int(os.getenv("DB_CONN_MAX_AGE", "60"))
    except ValueError as error:
        raise ImproperlyConfigured("DB_CONN_MAX_AGE must be a non-negative integer.") from error
    if connection_max_age < 0:
        raise ImproperlyConfigured("DB_CONN_MAX_AGE must be a non-negative integer.")

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["DB_NAME"].strip(),
            "USER": os.environ["DB_USER"].strip(),
            "PASSWORD": os.environ["DB_PASSWORD"],
            "HOST": os.environ["DB_HOST"].strip(),
            "PORT": database_port,
            "CONN_MAX_AGE": connection_max_age,
            "OPTIONS": {"sslmode": sslmode},
        }
    }
else:
    raise ImproperlyConfigured("DB_ENGINE must be sqlite or postgresql.")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
cookie_samesite = os.getenv("SESSION_COOKIE_SAMESITE", "Lax").strip()
if cookie_samesite not in {"Strict", "Lax", "None"}:
    raise ImproperlyConfigured("SESSION_COOKIE_SAMESITE must be Strict, Lax, or None.")
if cookie_samesite == "None" and DEBUG:
    raise ImproperlyConfigured("SESSION_COOKIE_SAMESITE=None requires secure cookies and DJANGO_DEBUG=False.")
SESSION_COOKIE_SAMESITE = cookie_samesite
CSRF_COOKIE_SAMESITE = cookie_samesite

frontend_origin_value = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173" if DEBUG else "")
frontend_origins = [origin.strip() for origin in frontend_origin_value.split(",") if origin.strip()]
if not frontend_origins or any("*" in origin for origin in frontend_origins):
    raise ImproperlyConfigured("FRONTEND_ORIGIN must contain explicit trusted origins; wildcards are not allowed.")
for origin in frontend_origins:
    parsed_origin = urlsplit(origin)
    if parsed_origin.scheme not in {"http", "https"} or not parsed_origin.netloc or parsed_origin.path not in {"", "/"}:
        raise ImproperlyConfigured("FRONTEND_ORIGIN entries must be explicit HTTP(S) origins without paths.")
    if parsed_origin.username or parsed_origin.password:
        raise ImproperlyConfigured("FRONTEND_ORIGIN must not contain credentials.")
    if not DEBUG and parsed_origin.scheme != "https":
        raise ImproperlyConfigured("Production FRONTEND_ORIGIN entries must use HTTPS.")
CORS_ALLOWED_ORIGINS = frontend_origins
CSRF_TRUSTED_ORIGINS = frontend_origins
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
