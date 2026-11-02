import json
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.utils import timezone
from django.urls import reverse

from accounts.models import AuditEvent, User
from clients.models import Client as ClientRecord

from .models import Lead, LeadActivity, LeadSource


class CrmApiTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.admin = User.objects.create_superuser("crm-admin@example.test", "Synthetic-Crm-Admin-753!")
        self.team_one = User.objects.create_user("crm-team-one@example.test", "Synthetic-Crm-Team-753!")
        self.team_two = User.objects.create_user("crm-team-two@example.test", "Synthetic-Crm-Team-754!")
        self.team_group, _ = Group.objects.get_or_create(name="Team")
        self.team_one.groups.add(self.team_group)
        self.team_two.groups.add(self.team_group)
        self.active_source = LeadSource.objects.create(name=f"Website {uuid4()}")
        self.inactive_source = LeadSource.objects.create(name=f"Referral {uuid4()}", is_active=False)

    def csrf_token(self):
        response = self.client.get(reverse("auth-csrf"))
        self.assertEqual(response.status_code, 200)
        return response.json()["csrfToken"]

    def post_json(self, url, payload, csrf_token=None):
        headers = {}
        if csrf_token:
            headers["HTTP_X_CSRFTOKEN"] = csrf_token
        return self.client.post(url, data=json.dumps(payload), content_type="application/json", **headers)

    def patch_json(self, url, payload):
        return self.client.patch(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token(),
        )

    def create_lead(self, **overrides):
        values = {
            "name": f"Prospect {uuid4()}",
            "status": Lead.Status.NEW,
            "priority": Lead.Priority.NORMAL,
            "currency": "INR",
            "created_by": self.admin,
            **overrides,
        }
        return Lead.objects.create(**values)

    def test_anonymous_lead_access_is_denied(self):
        self.assertEqual(self.client.get(reverse("lead-list")).status_code, 403)

    def test_admin_can_create_lead_with_safe_audit_record(self):
        self.client.force_login(self.admin)

        response = self.post_json(
            reverse("lead-list"),
            {
                "name": "Mahi Prospect",
                "email": "PROSPECT@EXAMPLE.TEST",
                "company_name": "Mahi Labs",
                "source": str(self.active_source.id),
                "interested_service": "Consulting",
                "estimated_value": "12500.50",
                "currency": "inr",
            },
            self.csrf_token(),
        )

        self.assertEqual(response.status_code, 201)
        lead = Lead.objects.get(pk=response.json()["id"])
        self.assertEqual(lead.email, "prospect@example.test")
        self.assertEqual(lead.estimated_value, Decimal("12500.50"))
        self.assertEqual(lead.currency, "INR")
        self.assertEqual(lead.status, Lead.Status.NEW)
        self.assertEqual(lead.priority, Lead.Priority.NORMAL)
        self.assertEqual(lead.created_by, self.admin)
        self.assertTrue(AuditEvent.objects.filter(
            actor=self.admin,
            action=AuditEvent.Action.CRM_LEAD_CREATED,
            target_object_type="crm.lead",
            target_object_id=lead.id,
        ).exists())
        self.assertNotIn("password", response.content.decode().lower())

    def test_team_creation_assigns_to_self_and_rejects_reassignment(self):
        self.client.force_login(self.team_one)
        response = self.post_json(
            reverse("lead-list"),
            {"name": "Self assigned"},
            self.csrf_token(),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Lead.objects.get(pk=response.json()["id"]).assigned_to, self.team_one)

        response = self.post_json(
            reverse("lead-list"),
            {"name": "Invalid assignment", "assigned_to": str(self.team_two.pk)},
            self.csrf_token(),
        )
        self.assertEqual(response.status_code, 400)

    def test_team_only_sees_and_updates_assigned_leads(self):
        own_lead = self.create_lead(assigned_to=self.team_one)
        other_lead = self.create_lead(assigned_to=self.team_two)
        self.client.force_login(self.team_one)

        response = self.client.get(reverse("lead-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["id"], str(own_lead.id))
        self.assertEqual(self.client.get(reverse("lead-detail", args=[other_lead.id])).status_code, 404)
        self.assertEqual(self.patch_json(reverse("lead-detail", args=[other_lead.id]), {"name": "IDOR"}).status_code, 404)

        response = self.patch_json(reverse("lead-detail", args=[own_lead.id]), {"status": Lead.Status.CONTACTED})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], Lead.Status.CONTACTED)
        self.assertTrue(LeadActivity.objects.filter(lead=own_lead, kind=LeadActivity.Kind.STATUS_CHANGE).exists())

    def test_list_search_filter_ordering_and_pagination(self):
        first = self.create_lead(name="Acme Alpha", company_name="Acme", status=Lead.Status.QUALIFIED, priority=Lead.Priority.HIGH, assigned_to=self.team_one)
        self.create_lead(name="Acme Beta", company_name="Acme", status=Lead.Status.NEW, assigned_to=self.team_one)
        self.create_lead(name="Other", assigned_to=self.team_two)
        self.client.force_login(self.admin)

        response = self.client.get(reverse("lead-list"), {
            "search": "acme",
            "status": Lead.Status.QUALIFIED,
            "priority": Lead.Priority.HIGH,
            "ordering": "name",
            "limit": 1,
            "offset": 0,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["id"], str(first.id))
        self.assertEqual(
            self.client.get(reverse("lead-list"), {"ordering": "notes"}).status_code,
            400,
        )

    def test_invalid_lead_data_is_rejected(self):
        self.client.force_login(self.admin)
        negative_value = self.post_json(
            reverse("lead-list"),
            {"name": "Bad value", "estimated_value": "-1.00"},
            self.csrf_token(),
        )
        bad_currency = self.post_json(
            reverse("lead-list"),
            {"name": "Bad currency", "currency": "US"},
            self.csrf_token(),
        )
        unexpected_field = self.post_json(
            reverse("lead-list"),
            {"name": "Mass assignment", "created_by": str(self.team_one.pk)},
            self.csrf_token(),
        )

        self.assertEqual(negative_value.status_code, 400)
        self.assertEqual(bad_currency.status_code, 400)
        self.assertEqual(unexpected_field.status_code, 400)

    def test_follow_up_can_be_set_to_a_past_date(self):
        lead = self.create_lead(assigned_to=self.team_one, follow_up_date=timezone.localdate())
        self.client.force_login(self.team_one)

        response = self.patch_json(
            reverse("lead-detail", args=[lead.id]),
            {"follow_up_date": (timezone.localdate() - timedelta(days=1)).isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["follow_up_date"], (timezone.localdate() - timedelta(days=1)).isoformat())

    def test_team_can_read_active_sources_but_cannot_manage_them(self):
        self.client.force_login(self.team_one)
        response = self.client.get(reverse("lead-source-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([source["id"] for source in response.json()], [str(self.active_source.id)])
        self.assertEqual(
            self.post_json(reverse("lead-source-list"), {"name": "Unauthorized"}, self.csrf_token()).status_code,
            403,
        )

    def test_admin_can_manage_sources_and_audit_changes(self):
        self.client.force_login(self.admin)
        response = self.post_json(reverse("lead-source-list"), {"name": "Event"}, self.csrf_token())
        self.assertEqual(response.status_code, 201)
        source_id = response.json()["id"]
        response = self.patch_json(reverse("lead-source-detail", args=[source_id]), {"is_active": False})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AuditEvent.objects.filter(
            actor=self.admin,
            action=AuditEvent.Action.CRM_SOURCE_UPDATED,
            target_object_id=source_id,
        ).exists())

    def test_lead_activity_creation_and_history_are_scoped(self):
        lead = self.create_lead(assigned_to=self.team_one)
        self.client.force_login(self.team_one)
        response = self.post_json(
            reverse("lead-activity-list", args=[lead.id]),
            {"kind": LeadActivity.Kind.CALL, "description": "Called prospect"},
            self.csrf_token(),
        )
        self.assertEqual(response.status_code, 201)
        response = self.client.get(reverse("lead-activity-list", args=[lead.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["description"], "Called prospect")
        self.assertEqual(response.json()[0]["actor_email"], self.team_one.email)

    def test_team_can_archive_assigned_lead_and_admin_can_filter_archived(self):
        lead = self.create_lead(assigned_to=self.team_one)
        self.client.force_login(self.team_one)
        response = self.client.post(
            reverse("lead-archive", args=[lead.id]),
            data="{}",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(reverse("lead-list")).json()["count"], 0)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("lead-list"), {"include_archived": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["id"], str(lead.id))

    def test_non_won_lead_cannot_convert(self):
        lead = self.create_lead(assigned_to=self.team_one)
        self.client.force_login(self.team_one)

        response = self.post_json(reverse("lead-convert", args=[lead.id]), {}, self.csrf_token())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ClientRecord.objects.count(), 0)

    def test_won_lead_converts_to_new_client_once_and_audits(self):
        lead = self.create_lead(
            name="Nila Sharma",
            email="nila@example.test",
            company_name="Nila Works",
            phone="+919876543210",
            status=Lead.Status.WON,
            assigned_to=self.team_one,
        )
        self.client.force_login(self.team_one)

        response = self.post_json(reverse("lead-convert", args=[lead.id]), {}, self.csrf_token())
        self.assertEqual(response.status_code, 201)
        client_id = response.json()["client"]["id"]
        client_record = ClientRecord.objects.get(pk=client_id)
        lead.refresh_from_db()
        self.assertEqual(lead.converted_client, client_record)
        self.assertEqual(client_record.created_from_lead, lead)
        self.assertTrue(AuditEvent.objects.filter(
            actor=self.team_one,
            action=AuditEvent.Action.CRM_LEAD_CONVERTED,
            target_object_type="crm.lead",
            target_object_id=lead.id,
        ).exists())

        repeated = self.post_json(reverse("lead-convert", args=[lead.id]), {}, self.csrf_token())
        self.assertEqual(repeated.status_code, 409)
        self.assertEqual(ClientRecord.objects.count(), 1)

    def test_existing_client_duplicate_is_reported_without_creation(self):
        existing = ClientRecord.objects.create(display_name="Existing", email="duplicate@example.test")
        lead = self.create_lead(
            name="Duplicate Prospect",
            email="DUPLICATE@example.test",
            status=Lead.Status.WON,
            assigned_to=self.team_one,
        )
        self.client.force_login(self.team_one)

        response = self.post_json(reverse("lead-convert", args=[lead.id]), {}, self.csrf_token())

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "POSSIBLE_DUPLICATE_CLIENT")
        self.assertEqual(response.json()["candidates"][0]["id"], str(existing.id))
        self.assertEqual(ClientRecord.objects.count(), 1)

    def test_lead_can_convert_to_an_explicit_existing_client(self):
        existing = ClientRecord.objects.create(display_name="Existing client")
        lead = self.create_lead(name="Existing client", status=Lead.Status.WON, assigned_to=self.team_one)
        self.client.force_login(self.team_one)

        response = self.post_json(
            reverse("lead-convert", args=[lead.id]),
            {"existing_client_id": str(existing.id)},
            self.csrf_token(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json()["created_new_client"])
        self.assertEqual(response.json()["client"]["id"], str(existing.id))
        self.assertEqual(ClientRecord.objects.count(), 1)

    def test_client_created_from_lead_reference_is_unique(self):
        lead = self.create_lead(status=Lead.Status.WON)
        ClientRecord.objects.create(display_name="First", created_from_lead=lead)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ClientRecord.objects.create(display_name="Second", created_from_lead=lead)