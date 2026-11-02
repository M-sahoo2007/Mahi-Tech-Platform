import json
import os
import subprocess
import sys
from pathlib import Path
from time import sleep
from urllib.parse import urlsplit
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.test import Client, SimpleTestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse

from .models import normalize_email
from .views import _login_cache_keys


class DjangoCacheUnitTests(SimpleTestCase):
    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "mahi-cache-unit-tests",
            }
        }
    )
    def test_cache_set_get_delete(self):
        key = f"cache-unit:{uuid4()}"

        cache.set(key, "available", timeout=10)
        self.assertEqual(cache.get(key), "available")
        cache.delete(key)
        self.assertIsNone(cache.get(key))


class CacheConfigurationTests(SimpleTestCase):
    backend_dir = Path(__file__).resolve().parents[1]

    def run_settings_probe(self, script, overrides, removed=()):
        environment = os.environ.copy()
        environment["PYTHON_DOTENV_DISABLED"] = "1"
        for name in (
            "DJANGO_DEBUG",
            "DJANGO_SECRET_KEY",
            "DJANGO_ALLOWED_HOSTS",
            "DB_ENGINE",
            "SQLITE_DB_NAME",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
            "DB_HOST",
            "DB_PORT",
            "DB_SSLMODE",
            "FRONTEND_ORIGIN",
            "SESSION_COOKIE_SAMESITE",
            "CACHE_URL",
        ):
            environment.pop(name, None)
        environment.update(overrides)
        for name in removed:
            environment.pop(name, None)

        return subprocess.run(
            [sys.executable, "-c", script],
            cwd=self.backend_dir,
            env=environment,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

    def test_development_fallback_is_local_memory_and_not_legacy_database(self):
        result = self.run_settings_probe(
            "import config.settings as s; print(s.CACHES['default']['BACKEND']); print(s.DATABASES['default']['NAME'])",
            {
                "DJANGO_DEBUG": "True",
                "DJANGO_SECRET_KEY": "synthetic-development-settings-test-key",
                "DB_ENGINE": "sqlite",
                "SQLITE_DB_NAME": "cache-settings-test.sqlite3",
                "FRONTEND_ORIGIN": "http://localhost:5173",
            },
            removed=("CACHE_URL",),
        )

        self.assertEqual(result.returncode, 0, "Development settings should load without a Redis URL.")
        self.assertIn("django.core.cache.backends.locmem.LocMemCache", result.stdout)
        self.assertIn("cache-settings-test.sqlite3", result.stdout)
        self.assertNotIn("db.sqlite3", result.stdout)

    def production_overrides(self):
        return {
            "DJANGO_DEBUG": "False",
            "DJANGO_SECRET_KEY": "synthetic-production-config-test-key-not-a-secret-0123456789-abcdefgh",
            "DJANGO_ALLOWED_HOSTS": "app.example.invalid",
            "DB_ENGINE": "postgresql",
            "DB_NAME": "synthetic_db",
            "DB_USER": "synthetic_user",
            "DB_PASSWORD": "synthetic-password-not-a-credential",
            "DB_HOST": "db.validation.invalid",
            "DB_PORT": "5432",
            "DB_SSLMODE": "require",
            "FRONTEND_ORIGIN": "https://app.example.invalid",
            "SESSION_COOKIE_SAMESITE": "Lax",
        }

    def test_production_requires_cache_url(self):
        result = self.run_settings_probe(
            "import config.settings",
            self.production_overrides(),
            removed=("CACHE_URL",),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Production requires CACHE_URL", result.stderr)

    def test_production_rejects_non_tls_redis_url(self):
        result = self.run_settings_probe(
            "import config.settings",
            {**self.production_overrides(), "CACHE_URL": "redis://127.0.0.1:6379/0"},
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Production CACHE_URL must use rediss:// TLS", result.stderr)

    def test_production_accepts_tls_cache_configuration_without_connecting(self):
        result = self.run_settings_probe(
            "import config.settings as s; print(s.CACHES['default']['BACKEND']); print(s.CACHES['default']['OPTIONS']['CLIENT_CLASS'])",
            {**self.production_overrides(), "CACHE_URL": "rediss://cache.example.invalid:6380/0"},
        )

        self.assertEqual(result.returncode, 0, "TLS Redis settings should load without opening a connection.")
        self.assertIn("django_redis.cache.RedisCache", result.stdout)
        self.assertIn("django_redis.client.DefaultClient", result.stdout)


redis_cache_backend = settings.CACHES.get("default", {}).get("BACKEND", "")
redis_cache_url = settings.CACHES.get("default", {}).get("LOCATION", "")
redis_cache_host = urlsplit(redis_cache_url).hostname if redis_cache_url else None
redis_integration_enabled = (
    os.getenv("RUN_REDIS_INTEGRATION_TESTS") == "1"
    and redis_cache_backend == "django_redis.cache.RedisCache"
    and redis_cache_host in {"localhost", "127.0.0.1", "::1"}
)


class RedisIntegrationTests(SimpleTestCase):
    __unittest_skip__ = not redis_integration_enabled
    __unittest_skip_why__ = "Requires explicit opt-in and CACHE_URL pointing to loopback Redis."

    def subprocess_cache_set(self, key, value, timeout):
        code = (
            "import os,sys; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); "
            "import django; django.setup(); from django.core.cache import cache; "
            "cache.set(sys.argv[1], int(sys.argv[2]), timeout=int(sys.argv[3]))"
        )
        result = subprocess.run(
            [sys.executable, "-c", code, key, value, str(timeout)],
            cwd=Path(__file__).resolve().parents[1],
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, "A separate Django process could not write the Redis cache key.")

    def test_redis_connectivity_and_cache_set_get_delete(self):
        client = cache.client.get_client(write=True)
        self.assertTrue(client.ping())
        key = f"redis-integration:{uuid4()}"
        self.addCleanup(cache.delete, key)

        self.assertTrue(cache.set(key, "connected", timeout=20))
        self.assertEqual(cache.get(key), "connected")
        self.assertTrue(cache.delete(key))
        self.assertIsNone(cache.get(key))

    def test_login_throttle_counter_is_shared_across_django_processes(self):
        email = f"redis-process-{uuid4()}@example.invalid"
        request = RequestFactory().post("/api/auth/login/", REMOTE_ADDR="127.0.0.1")
        email_key, address_key = _login_cache_keys(normalize_email(email), request)
        self.addCleanup(cache.delete_many, (email_key, address_key))
        self.subprocess_cache_set(
            email_key,
            str(settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS),
            settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        )
        self.assertEqual(cache.get(email_key), settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS)

        response = Client().post(
            reverse("auth-login"),
            data=json.dumps({"email": email, "password": "synthetic-invalid-password"}),
            content_type="application/json",
            REMOTE_ADDR="127.0.0.1",
        )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["detail"], "Unable to sign in right now. Please try again later.")

    def test_throttle_window_expires_and_recovers(self):
        email = f"redis-expiry-{uuid4()}@example.invalid"
        request = RequestFactory().post("/api/auth/login/", REMOTE_ADDR="127.0.0.1")
        email_key, address_key = _login_cache_keys(normalize_email(email), request)
        self.addCleanup(cache.delete_many, (email_key, address_key))
        self.assertTrue(cache.set(email_key, settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS, timeout=1))
        self.assertGreaterEqual(cache.get(email_key), settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS)

        sleep(1.1)

        self.assertEqual(cache.get(email_key, 0), 0)

    def test_cache_reconnects_after_connection_pool_disconnect(self):
        redis_client = cache.client.get_client(write=True)
        self.assertTrue(redis_client.ping())
        redis_client.connection_pool.disconnect()

        key = f"redis-reconnect:{uuid4()}"
        self.addCleanup(cache.delete, key)
        self.assertTrue(cache.set(key, "reconnected", timeout=20))
        self.assertEqual(cache.get(key), "reconnected")