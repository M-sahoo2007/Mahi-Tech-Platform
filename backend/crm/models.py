import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class LeadSource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        permissions = [("manage_lead_sources", "Can manage lead sources")]

    def __str__(self):
        return self.name


class Lead(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        PROPOSAL_SENT = "proposal_sent", "Proposal Sent"
        NEGOTIATION = "negotiation", "Negotiation"
        WON = "won", "Won"
        LOST = "lost", "Lost"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=40, blank=True)
    company_name = models.CharField(max_length=200, blank=True, db_index=True)
    source = models.ForeignKey(
        LeadSource,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
    )
    interested_service = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.NEW, db_index=True)
    priority = models.CharField(max_length=12, choices=Priority.choices, default=Priority.NORMAL, db_index=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_leads",
    )
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="INR")
    follow_up_date = models.DateField(null=True, blank=True, db_index=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_leads",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_leads",
    )
    converted_client = models.ForeignKey(
        "clients.Client",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="converted_leads",
    )
    converted_at = models.DateTimeField(null=True, blank=True)
    converted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="converted_leads",
    )
    archived_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "id")
        indexes = [
            models.Index(fields=("status", "follow_up_date"), name="crm_lead_status_follow_idx"),
            models.Index(fields=("assigned_to", "status", "follow_up_date"), name="crm_lead_owner_queue_idx"),
            models.Index(fields=("priority", "follow_up_date"), name="crm_lead_priority_follow_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(estimated_value__isnull=True) | Q(estimated_value__gte=0),
                name="crm_lead_value_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(converted_client__isnull=True, converted_at__isnull=True)
                | Q(converted_client__isnull=False, converted_at__isnull=False),
                name="crm_lead_conversion_pair",
            ),
        ]
        permissions = [("view_all_leads", "Can view all leads")]

    def __str__(self):
        return self.company_name or self.name


class LeadActivity(models.Model):
    class Kind(models.TextChoices):
        NOTE = "note", "Note"
        CALL = "call", "Call"
        EMAIL = "email", "Email"
        STATUS_CHANGE = "status_change", "Status change"
        PRIORITY_CHANGE = "priority_change", "Priority change"
        ASSIGNMENT = "assignment", "Assignment"
        FOLLOW_UP = "follow_up", "Follow-up"
        CONVERSION = "conversion", "Conversion"
        DETAILS_UPDATED = "details_updated", "Details updated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="activities")
    kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.NOTE)
    description = models.TextField()
    previous_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lead_activities",
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-created_at", "id")
        indexes = [models.Index(fields=("lead", "created_at"), name="crm_activity_timeline_idx")]

    def __str__(self):
        return f"{self.get_kind_display()} for {self.lead_id}"