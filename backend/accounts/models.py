import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.conf import settings
from django.utils import timezone


class AuditEvent(models.Model):
    class Action(models.TextChoices):
        ACCOUNT_LISTED = "account.listed", "Account list accessed"
        ACCOUNT_CREATED = "account.created", "Account created"
        ACCOUNT_ACTIVATED = "account.activated", "Account activated"
        ACCOUNT_DEACTIVATED = "account.deactivated", "Account deactivated"
        ROLE_ASSIGNED = "account.role_assigned", "Account role assigned"
        ACCESS_DENIED = "account.access_denied", "Account management access denied"
        CRM_LEAD_CREATED = "crm.lead.created", "CRM lead created"
        CRM_LEAD_UPDATED = "crm.lead.updated", "CRM lead updated"
        CRM_LEAD_ARCHIVED = "crm.lead.archived", "CRM lead archived"
        CRM_LEAD_CONVERTED = "crm.lead.converted", "CRM lead converted"
        CRM_SOURCE_CREATED = "crm.source.created", "CRM lead source created"
        CRM_SOURCE_UPDATED = "crm.source.updated", "CRM lead source updated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="account_audit_events",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="account_audit_targets",
    )
    action = models.CharField(max_length=40, choices=Action.choices)
    target_object_type = models.CharField(max_length=100, blank=True)
    target_object_id = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        default_permissions = ("view",)
        indexes = [
            models.Index(fields=("target_object_type", "target_object_id"), name="audit_object_target_idx"),
        ]

    def __str__(self):
        return f"{self.action} at {self.created_at.isoformat()}"

def normalize_email(email):
    return BaseUserManager.normalize_email(email).strip().lower()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(email=normalize_email(username))

    def create_user(self, email, password=None, **extra_fields):
        if not email or not email.strip():
            raise ValueError("An email address is required.")
        user = self.model(email=normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        permissions = [("manage_users", "Can manage team accounts")]

    def clean(self):
        super().clean()
        if self.email:
            self.email = normalize_email(self.email)

    def save(self, *args, **kwargs):
        if self.email:
            self.email = normalize_email(self.email)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email