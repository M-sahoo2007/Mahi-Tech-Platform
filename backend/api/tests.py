from datetime import datetime

from django.contrib.auth.models import Group
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from accounts.models import User


class HealthEndpointTests(SimpleTestCase):
    def test_health_returns_expected_json(self):
        response = self.client.get(reverse("api-health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "Mahi-Tech Platform API")
        self.assertEqual(payload["message"], "Backend is running")
        self.assertIsInstance(payload["timestamp"], str)
        self.assertIsNotNone(datetime.fromisoformat(payload["timestamp"]))


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "mahi-dashboard-api-tests",
        }
    }
)
class DashboardSummaryApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin@example.com", "secure-password")
        team_group, _ = Group.objects.get_or_create(name="Team")
        self.active_team = User.objects.create_user("active-team@example.com", "secure-password")
        self.active_team.groups.add(team_group)
        self.inactive_team = User.objects.create_user(
            "inactive-team@example.com",
            "secure-password",
            is_active=False,
        )
        self.inactive_team.groups.add(team_group)

    def test_anonymous_dashboard_access_is_denied(self):
        response = self.client.get(reverse("dashboard-summary"))

        self.assertEqual(response.status_code, 403)

    def test_admin_receives_real_team_counts_and_safe_profile(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard-summary"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["current_user"], {
            "id": str(self.admin.pk),
            "email": "admin@example.com",
            "role": "admin",
        })
        self.assertEqual(payload["team_accounts"], {"total": 2, "active": 1})
        self.assertEqual(payload["system"], {
            "api": "connected",
            "cache": "connected",
            "cache_backend": "local",
        })
        self.assertNotIn("password", response.content.decode().lower())
        self.assertNotIn("active-team@example.com", response.content.decode())

    def test_team_member_can_access_dashboard_without_admin_data(self):
        self.client.force_login(self.active_team)

        response = self.client.get(reverse("dashboard-summary"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["current_user"]["role"], "team")
        self.assertEqual(payload["team_accounts"], {"total": 2, "active": 1})