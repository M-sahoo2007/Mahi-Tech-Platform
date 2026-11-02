import re

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from clients.models import Client

from .models import Lead, LeadActivity, LeadSource

User = get_user_model()


class LeadSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadSource
        fields = ("id", "name", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        unexpected = set(self.initial_data) - {"name", "is_active"}
        if unexpected:
            raise serializers.ValidationError({field: "This field cannot be set." for field in sorted(unexpected)})
        return attrs


class LeadSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True, allow_null=True)
    assigned_to_email = serializers.EmailField(source="assigned_to.email", read_only=True, allow_null=True)
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True, allow_null=True)
    converted_client_name = serializers.CharField(source="converted_client.display_name", read_only=True, allow_null=True)
    source = serializers.PrimaryKeyRelatedField(
        queryset=LeadSource.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True, groups__name="Team").distinct(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Lead
        fields = (
            "id",
            "name",
            "email",
            "phone",
            "company_name",
            "source",
            "source_name",
            "interested_service",
            "status",
            "priority",
            "assigned_to",
            "assigned_to_email",
            "estimated_value",
            "currency",
            "follow_up_date",
            "notes",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
            "archived_at",
            "converted_client",
            "converted_client_name",
            "converted_at",
        )
        read_only_fields = (
            "id",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
            "archived_at",
            "converted_client",
            "converted_client_name",
            "converted_at",
        )

    def validate_email(self, value):
        return value.strip().lower()

    def validate_currency(self, value):
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", normalized):
            raise serializers.ValidationError("Currency must be a three-letter ISO code.")
        return normalized

    def validate_estimated_value(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Estimated value cannot be negative.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        allowed = {
            "name",
            "email",
            "phone",
            "company_name",
            "source",
            "interested_service",
            "status",
            "priority",
            "assigned_to",
            "estimated_value",
            "currency",
            "follow_up_date",
            "notes",
        }
        unexpected = set(self.initial_data) - allowed
        if unexpected:
            raise serializers.ValidationError({field: "This field cannot be set." for field in sorted(unexpected)})
        if not (request.user.is_superuser or request.user.has_perm("accounts.manage_users")):
            if "assigned_to" in self.initial_data:
                raise serializers.ValidationError({"assigned_to": "Team members cannot assign leads to other users."})
        return attrs


class LeadActivitySerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, allow_null=True)

    class Meta:
        model = LeadActivity
        fields = ("id", "kind", "description", "previous_values", "new_values", "actor", "actor_email", "created_at")
        read_only_fields = ("id", "previous_values", "new_values", "actor", "actor_email", "created_at")

    def validate(self, attrs):
        unexpected = set(self.initial_data) - {"kind", "description"}
        if unexpected:
            raise serializers.ValidationError({field: "This field cannot be set." for field in sorted(unexpected)})
        return attrs

    def validate_kind(self, value):
        system_kinds = {LeadActivity.Kind.STATUS_CHANGE, LeadActivity.Kind.PRIORITY_CHANGE, LeadActivity.Kind.ASSIGNMENT, LeadActivity.Kind.CONVERSION, LeadActivity.Kind.DETAILS_UPDATED}
        if value in system_kinds:
            raise serializers.ValidationError("This activity type is recorded by the system.")
        return value


class LeadConversionSerializer(serializers.Serializer):
    existing_client_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if set(self.initial_data) - {"existing_client_id"}:
            raise serializers.ValidationError("Only existing_client_id may be supplied.")
        return attrs


class CrmDashboardSerializer(serializers.Serializer):
    total = serializers.IntegerField(min_value=0)
    by_status = serializers.DictField(child=serializers.IntegerField(min_value=0))
    follow_ups_due = serializers.IntegerField(min_value=0)


class ClientConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ("id", "display_name", "company_name", "email", "phone")
        read_only_fields = fields