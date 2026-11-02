import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=40, blank=True, db_index=True)
    address_line_1 = models.CharField(max_length=200, blank=True)
    address_line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=24, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_crm_clients",
    )
    created_from_lead = models.OneToOneField(
        "crm.Lead",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="created_client",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_name",)

    def __str__(self):
        return self.company_name or self.display_name