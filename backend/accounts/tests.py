import json
from time import sleep
from uuid import UUID
from unittest.mock import patch

from django.contrib.auth import authenticate
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import AuditEvent, User


class UserManagerTests(TestCase):
    def test_create_user_normalizes_email_and_hashes_password(self):
        user = User.objects.create_user("  Mahi.Owner@Example.COM  ", "secure-password")

        self.assertEqual(user.email, "mahi.owner@example.com")
        self.assertIsInstance(user.pk, UUID)
        self.assertTrue(User._meta.get_field("email").unique)
        self.assertNotEqual(user.password, "secure-password")
        self.assertTrue(user.check_password("secure-password"))
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

    def test_create_user_requires_email(self):
        with self.assertRaisesMessage(ValueError, "An email address is required."):
            User.objects.create_user("", "secure-password")

    def test_create_superuser_sets_required_flags(self):
        user = User.objects.create_superuser("owner@example.com", "secure-password")

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_superuser_rejects_invalid_flags(self):
        with self.assertRaisesMessage(ValueError, "A superuser must have is_staff=True."):
            User.objects.create_superuser("owner@example.com", "secure-password", is_staff=False)

    def test_authentication_uses_normalized_email(self):
        User.objects.create_user("owner@example.com", "secure-password")

        user = authenticate(email="OWNER@EXAMPLE.COM", password="secure-password")

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "owner@example.com")

    def test_authentication_rejects_incorrect_password(self):
        User.objects.create_user("owner@example.com", "secure-password")

        user = authenticate(email="owner@example.com", password="incorrect-password")

        self.assertIsNone(user)

    def test_authentication_rejects_inactive_user(self):
        User.objects.create_user("owner@example.com", "secure-password", is_active=False)

        user = authenticate(email="owner@example.com", password="secure-password")

        self.assertIsNone(user)


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "mahi-auth-test-cache",
        }
    }
)
class AuthenticationApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user("owner@example.com", "secure-password")

    def csrf_token(self):
        response = self.client.get(
            reverse("auth-csrf"),
            HTTP_ORIGIN="http://localhost:5173",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["csrfToken"]

    def post_json(self, url, payload, csrf_token=None):
        headers = {"HTTP_ORIGIN": "http://localhost:5173"}
        if csrf_token:
            headers["HTTP_X_CSRFTOKEN"] = csrf_token
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            **headers,
        )

    def test_csrf_endpoint_sets_cookie_and_allows_credentialed_cors(self):
        response = self.client.get(
            reverse("auth-csrf"),
            HTTP_ORIGIN="http://localhost:5173",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["csrfToken"])
        self.assertEqual(response["Access-Control-Allow-Origin"], "http://localhost:5173")
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")
        csrf_cookie = response.cookies["csrftoken"]
        self.assertTrue(csrf_cookie["httponly"])
        self.assertEqual(csrf_cookie["samesite"], "Lax")

    def test_login_requires_csrf_token(self):
        response = self.post_json(
            reverse("auth-login"),
            {"email": "owner@example.com", "password": "secure-password"},
        )

        self.assertEqual(response.status_code, 403)

    def test_successful_login_sets_http_only_session_cookie(self):
        response = self.post_json(
            reverse("auth-login"),
            {"email": "OWNER@EXAMPLE.COM", "password": "secure-password"},
            self.csrf_token(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["email"], "owner@example.com")
        self.assertNotIn("password", response.json()["user"])
        session_cookie = response.cookies["sessionid"]
        self.assertTrue(session_cookie["httponly"])
        self.assertEqual(session_cookie["samesite"], "Lax")
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 200)

    def test_login_rejects_incorrect_password(self):
        response = self.post_json(
            reverse("auth-login"),
            {"email": "owner@example.com", "password": "incorrect-password"},
            self.csrf_token(),
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid email or password.")

    def test_login_rejects_inactive_user(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.post_json(
            reverse("auth-login"),
            {"email": "owner@example.com", "password": "secure-password"},
            self.csrf_token(),
        )

        self.assertEqual(response.status_code, 401)

    @override_settings(LOGIN_RATE_LIMIT_MAX_ATTEMPTS=3, LOGIN_RATE_LIMIT_WINDOW_SECONDS=900)
    def test_login_throttles_and_successful_login_resets_failures(self):
        for _ in range(2):
            response = self.post_json(
                reverse("auth-login"),
                {"email": "owner@example.com", "password": "incorrect-password"},
                self.csrf_token(),
            )
            self.assertEqual(response.status_code, 401)

        response = self.post_json(
            reverse("auth-login"),
            {"email": "owner@example.com", "password": "secure-password"},
            self.csrf_token(),
        )
        self.assertEqual(response.status_code, 200)

        for _ in range(3):
            response = self.post_json(
                reverse("auth-login"),
                {"email": "owner@example.com", "password": "incorrect-password"},
                self.csrf_token(),
            )
            self.assertEqual(response.status_code, 401)

        response = self.post_json(
            reverse("auth-login"),
            {"email": "owner@example.com", "password": "incorrect-password"},
            self.csrf_token(),
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "900")
        self.assertEqual(response.json()["detail"], "Unable to sign in right now. Please try again later.")

    @patch("accounts.views.cache.get", side_effect=RuntimeError("cache unavailable"))
    def test_login_fails_closed_when_cache_is_unavailable(self, _cache_get):
        response = self.post_json(
            reverse("auth-login"),
            {"email": "owner@example.com", "password": "secure-password"},
            self.csrf_token(),
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Sign-in is temporarily unavailable.")

    @override_settings(LOGIN_RATE_LIMIT_MAX_ATTEMPTS=1, LOGIN_RATE_LIMIT_WINDOW_SECONDS=1)
    def test_login_throttle_recovers_after_window_expires(self):
        invalid_response = self.post_json(
            reverse("auth-login"),
            {"email": "owner@example.com", "password": "incorrect-password"},
            self.csrf_token(),
        )
        blocked_response = self.post_json(
            reverse("auth-login"),
            {"email": "owner@example.com", "password": "secure-password"},
            self.csrf_token(),
        )
        self.assertEqual(invalid_response.status_code, 401)
        self.assertEqual(blocked_response.status_code, 429)

        sleep(1.1)
        recovered_response = self.post_json(
            reverse("auth-login"),
            {"email": "owner@example.com", "password": "secure-password"},
            self.csrf_token(),
        )

        self.assertEqual(recovered_response.status_code, 200)

    def test_logout_invalidates_session(self):
        self.client.force_login(self.user)
        response = self.post_json(reverse("auth-logout"), {}, self.csrf_token())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(reverse("auth-me")).status_code, 401)

    def test_current_user_rejects_anonymous_requests(self):
        response = self.client.get(reverse("auth-me"))

        self.assertEqual(response.status_code, 401)

    def test_public_registration_route_does_not_exist(self):
        response = self.client.post(
            "/api/auth/register/",
            data=json.dumps({"email": "new@example.com", "password": "Long-Test-Passphrase-907!"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)


class AccountManagementApiTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.admin = User.objects.create_superuser("admin@example.com", "secure-password")
        self.team = User.objects.create_user("team@example.com", "secure-password")
        team_group, _ = Group.objects.get_or_create(name="Team")
        self.team.groups.add(team_group)

    def csrf_token(self):
        return self.client.get(reverse("auth-csrf")).json()["csrfToken"]

    def post_json(self, url, payload, csrf_token):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    def test_team_member_cannot_list_or_create_accounts(self):
        self.client.force_login(self.team)
        response = self.client.get(reverse("account-collection"))

        self.assertEqual(response.status_code, 403)

        response = self.post_json(
            reverse("account-collection"),
            {"email": "new@example.com", "password": "Long-Test-Passphrase-907!", "role": "team"},
            self.csrf_token(),
        )
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_cannot_access_account_management(self):
        response = self.client.get(reverse("account-collection"))

        self.assertEqual(response.status_code, 401)

    def test_admin_can_create_team_account_without_elevating_it(self):
        self.client.force_login(self.admin)
        response = self.post_json(
            reverse("account-collection"),
            {"email": "new@example.com", "password": "Long-Test-Passphrase-907!", "role": "team"},
            self.csrf_token(),
        )

        self.assertEqual(response.status_code, 201)
        created_user = User.objects.get(email="new@example.com")
        self.assertTrue(created_user.check_password("Long-Test-Passphrase-907!"))
        self.assertFalse(created_user.is_superuser)
        self.assertFalse(created_user.is_staff)
        self.assertNotIn("password", response.json()["user"])

    def test_admin_can_assign_admin_group_without_superuser_status(self):
        self.client.force_login(self.admin)
        create_response = self.post_json(
            reverse("account-collection"),
            {"email": "new@example.com", "password": "Long-Test-Passphrase-907!", "role": "team"},
            self.csrf_token(),
        )
        created_id = create_response.json()["user"]["id"]
        update_response = self.client.patch(
            reverse("account-detail", args=[created_id]),
            data=json.dumps({"role": "admin"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token(),
        )

        self.assertEqual(update_response.status_code, 200)
        created_user = User.objects.get(pk=created_id)
        self.assertTrue(created_user.has_perm("accounts.manage_users"))
        self.assertFalse(created_user.is_superuser)
        self.client.force_login(created_user)
        self.assertEqual(self.client.get(reverse("account-collection")).status_code, 200)

    def test_admin_cannot_assign_unapproved_fields(self):
        self.client.force_login(self.admin)
        response = self.post_json(
            reverse("account-collection"),
            {
                "email": "new@example.com",
                "password": "Long-Test-Passphrase-907!",
                "role": "team",
                "is_superuser": True,
            },
            self.csrf_token(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="new@example.com").exists())

    def test_admin_rejects_non_string_role(self):
        self.client.force_login(self.admin)
        response = self.post_json(
            reverse("account-collection"),
            {"email": "new@example.com", "password": "Long-Test-Passphrase-907!", "role": []},
            self.csrf_token(),
        )

        self.assertEqual(response.status_code, 400)

    def test_management_actions_are_audited_without_credentials(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("account-collection")).status_code, 200)
        create_response = self.post_json(
            reverse("account-collection"),
            {"email": "audit-target@example.com", "password": "Long-Test-Passphrase-907!", "role": "team"},
            self.csrf_token(),
        )
        target_id = create_response.json()["user"]["id"]
        update_url = reverse("account-detail", args=[target_id])
        demote_response = self.client.patch(
            update_url,
            data=json.dumps({"role": "admin", "is_active": False}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token(),
        )
        self.assertEqual(demote_response.status_code, 200)
        activate_response = self.client.patch(
            update_url,
            data=json.dumps({"is_active": True}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token(),
        )
        self.assertEqual(activate_response.status_code, 200)

        events = AuditEvent.objects.filter(target_user_id=target_id)
        actions = set(events.values_list("action", flat=True))
        self.assertEqual(
            actions,
            {
                AuditEvent.Action.ACCOUNT_CREATED,
                AuditEvent.Action.ROLE_ASSIGNED,
                AuditEvent.Action.ACCOUNT_DEACTIVATED,
                AuditEvent.Action.ACCOUNT_ACTIVATED,
            },
        )
        self.assertTrue(all(event.actor_id == self.admin.pk for event in events))
        self.assertNotIn("password", json.dumps(list(events.values_list("metadata", flat=True))).lower())
        self.assertNotIn("session", json.dumps(list(events.values_list("metadata", flat=True))).lower())
        self.assertTrue(AuditEvent.objects.filter(actor=self.admin, action=AuditEvent.Action.ACCOUNT_LISTED).exists())

    def test_denied_team_access_is_audited(self):
        self.client.force_login(self.team)
        response = self.client.get(reverse("account-collection"))

        self.assertEqual(response.status_code, 403)
        event = AuditEvent.objects.get(actor=self.team, action=AuditEvent.Action.ACCESS_DENIED)
        self.assertEqual(event.metadata, {})