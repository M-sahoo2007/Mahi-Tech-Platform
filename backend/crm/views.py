from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import AuditEvent
from clients.models import Client

from .models import Lead, LeadActivity, LeadSource
from .permissions import CanUseCrm, IsCrmAdmin, is_admin, is_team_member
from .serializers import (
    ClientConversionSerializer,
    CrmDashboardSerializer,
    LeadActivitySerializer,
    LeadConversionSerializer,
    LeadSerializer,
    LeadSourceSerializer,
)

User = get_user_model()
LEAD_ORDERING_FIELDS = {"name", "created_at", "updated_at", "follow_up_date", "estimated_value", "priority", "status"}


def record_crm_audit(actor, action, target_type, target_id, metadata=None):
    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        target_object_type=target_type,
        target_object_id=target_id,
        metadata=metadata or {},
    )


def scoped_leads(user, include_archived=False):
    queryset = Lead.objects.select_related("source", "assigned_to", "created_by", "converted_client")
    if not is_admin(user):
        if not is_team_member(user):
            return queryset.none()
        queryset = queryset.filter(assigned_to=user)
    if not include_archived:
        queryset = queryset.filter(archived_at__isnull=True)
    return queryset


def get_scoped_lead_or_404(user, lead_id, include_archived=True, lock=False):
    queryset = scoped_leads(user, include_archived=include_archived)
    if lock:
        queryset = queryset.select_for_update()
    return get_object_or_404(queryset, pk=lead_id)


class LeadPagination(LimitOffsetPagination):
    default_limit = 25
    max_limit = 100


class LeadQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True, max_length=200)
    status = serializers.ChoiceField(choices=Lead.Status.choices, required=False)
    priority = serializers.ChoiceField(choices=Lead.Priority.choices, required=False)
    source = serializers.UUIDField(required=False)
    assigned_to = serializers.UUIDField(required=False)
    follow_up_after = serializers.DateField(required=False)
    follow_up_before = serializers.DateField(required=False)
    include_archived = serializers.BooleanField(required=False, default=False)
    ordering = serializers.CharField(required=False, default="-updated_at")

    def validate_ordering(self, value):
        field = value[1:] if value.startswith("-") else value
        if field not in LEAD_ORDERING_FIELDS:
            raise serializers.ValidationError("Unsupported ordering field.")
        return value

    def validate(self, attrs):
        if attrs.get("follow_up_after") and attrs.get("follow_up_before"):
            if attrs["follow_up_after"] > attrs["follow_up_before"]:
                raise serializers.ValidationError("follow_up_after must not be later than follow_up_before.")
        return attrs


class LeadListCreateView(APIView):
    permission_classes = [CanUseCrm]

    def get(self, request):
        query = LeadQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        if params.get("include_archived") and not is_admin(request.user):
            return Response({"detail": "Only administrators may include archived leads."}, status=status.HTTP_403_FORBIDDEN)

        leads = scoped_leads(request.user, include_archived=params.get("include_archived", False))
        if params.get("status"):
            leads = leads.filter(status=params["status"])
        if params.get("priority"):
            leads = leads.filter(priority=params["priority"])
        if params.get("source"):
            leads = leads.filter(source_id=params["source"])
        if params.get("assigned_to"):
            leads = leads.filter(assigned_to_id=params["assigned_to"])
        if params.get("follow_up_after"):
            leads = leads.filter(follow_up_date__gte=params["follow_up_after"])
        if params.get("follow_up_before"):
            leads = leads.filter(follow_up_date__lte=params["follow_up_before"])
        if params.get("search"):
            term = params["search"].strip()
            if term:
                leads = leads.filter(
                    Q(name__icontains=term)
                    | Q(email__icontains=term)
                    | Q(phone__icontains=term)
                    | Q(company_name__icontains=term)
                    | Q(interested_service__icontains=term)
                )
        leads = leads.order_by(params.get("ordering", "-updated_at"), "id")
        paginator = LeadPagination()
        page = paginator.paginate_queryset(leads, request, view=self)
        return paginator.get_paginated_response(LeadSerializer(page, many=True, context={"request": request}).data)

    def post(self, request):
        serializer = LeadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        assigned_to = request.user if is_team_member(request.user) and not is_admin(request.user) else serializer.validated_data.get("assigned_to")
        with transaction.atomic():
            lead = serializer.save(created_by=request.user, updated_by=request.user, assigned_to=assigned_to)
            LeadActivity.objects.create(
                lead=lead,
                kind=LeadActivity.Kind.NOTE,
                description="Lead created.",
                actor=request.user,
            )
            record_crm_audit(request.user, AuditEvent.Action.CRM_LEAD_CREATED, "crm.lead", lead.id)
        return Response(LeadSerializer(lead, context={"request": request}).data, status=status.HTTP_201_CREATED)


class LeadDetailView(APIView):
    permission_classes = [CanUseCrm]

    def get(self, request, lead_id):
        lead = get_scoped_lead_or_404(request.user, lead_id)
        return Response(LeadSerializer(lead, context={"request": request}).data)

    def patch(self, request, lead_id):
        lead = get_scoped_lead_or_404(request.user, lead_id)
        serializer = LeadSerializer(lead, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        previous = {
            "status": lead.status,
            "priority": lead.priority,
            "assigned_to": str(lead.assigned_to_id) if lead.assigned_to_id else None,
            "follow_up_date": lead.follow_up_date.isoformat() if lead.follow_up_date else None,
        }
        with transaction.atomic():
            lead = serializer.save(updated_by=request.user)
            current = {
                "status": lead.status,
                "priority": lead.priority,
                "assigned_to": str(lead.assigned_to_id) if lead.assigned_to_id else None,
                "follow_up_date": lead.follow_up_date.isoformat() if lead.follow_up_date else None,
            }
            changed = {key: (previous[key], current[key]) for key in previous if previous[key] != current[key]}
            if changed:
                for key, (old_value, new_value) in changed.items():
                    kind = {
                        "status": LeadActivity.Kind.STATUS_CHANGE,
                        "priority": LeadActivity.Kind.PRIORITY_CHANGE,
                        "assigned_to": LeadActivity.Kind.ASSIGNMENT,
                        "follow_up_date": LeadActivity.Kind.FOLLOW_UP,
                    }[key]
                    LeadActivity.objects.create(
                        lead=lead,
                        kind=kind,
                        description=f"{key.replace('_', ' ').title()} changed.",
                        previous_values={key: old_value},
                        new_values={key: new_value},
                        actor=request.user,
                    )
            else:
                LeadActivity.objects.create(
                    lead=lead,
                    kind=LeadActivity.Kind.DETAILS_UPDATED,
                    description="Lead details updated.",
                    actor=request.user,
                )
            record_crm_audit(
                request.user,
                AuditEvent.Action.CRM_LEAD_UPDATED,
                "crm.lead",
                lead.id,
                metadata={"changed_fields": sorted(changed) or ["details"]},
            )
        return Response(LeadSerializer(lead, context={"request": request}).data)


class LeadArchiveView(APIView):
    permission_classes = [CanUseCrm]

    def post(self, request, lead_id):
        with transaction.atomic():
            lead = get_scoped_lead_or_404(request.user, lead_id, include_archived=False, lock=True)
            lead.archived_at = timezone.now()
            lead.updated_by = request.user
            lead.save(update_fields=("archived_at", "updated_by", "updated_at"))
            LeadActivity.objects.create(
                lead=lead,
                kind=LeadActivity.Kind.DETAILS_UPDATED,
                description="Lead archived.",
                actor=request.user,
            )
            record_crm_audit(request.user, AuditEvent.Action.CRM_LEAD_ARCHIVED, "crm.lead", lead.id)
        return Response({"detail": "Lead archived."})


class LeadSourceListCreateView(APIView):
    permission_classes = [CanUseCrm]

    def get(self, request):
        sources = LeadSource.objects.all()
        if not is_admin(request.user):
            sources = sources.filter(is_active=True)
        return Response(LeadSourceSerializer(sources, many=True).data)

    def post(self, request):
        if not is_admin(request.user):
            return Response({"detail": "Administrator permission required."}, status=status.HTTP_403_FORBIDDEN)
        serializer = LeadSourceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            source = serializer.save()
            record_crm_audit(request.user, AuditEvent.Action.CRM_SOURCE_CREATED, "crm.lead_source", source.id)
        return Response(LeadSourceSerializer(source).data, status=status.HTTP_201_CREATED)


class LeadSourceDetailView(APIView):
    permission_classes = [CanUseCrm, IsCrmAdmin]

    def patch(self, request, source_id):
        source = get_object_or_404(LeadSource, pk=source_id)
        serializer = LeadSourceSerializer(source, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            source = serializer.save()
            record_crm_audit(request.user, AuditEvent.Action.CRM_SOURCE_UPDATED, "crm.lead_source", source.id)
        return Response(LeadSourceSerializer(source).data)


class LeadActivityListCreateView(APIView):
    permission_classes = [CanUseCrm]

    def get(self, request, lead_id):
        lead = get_scoped_lead_or_404(request.user, lead_id)
        activities = lead.activities.select_related("actor").order_by("-created_at", "id")
        return Response(LeadActivitySerializer(activities, many=True).data)

    def post(self, request, lead_id):
        lead = get_scoped_lead_or_404(request.user, lead_id)
        serializer = LeadActivitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            activity = serializer.save(lead=lead, actor=request.user)
            record_crm_audit(
                request.user,
                AuditEvent.Action.CRM_LEAD_UPDATED,
                "crm.lead",
                lead.id,
                metadata={"activity_id": str(activity.id), "activity_kind": activity.kind},
            )
        return Response(LeadActivitySerializer(activity).data, status=status.HTTP_201_CREATED)


class LeadConversionView(APIView):
    permission_classes = [CanUseCrm]

    def post(self, request, lead_id):
        input_serializer = LeadConversionSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        existing_client_id = input_serializer.validated_data.get("existing_client_id")
        try:
            with transaction.atomic():
                lead = get_scoped_lead_or_404(request.user, lead_id, lock=True)
                if lead.status != Lead.Status.WON:
                    return Response({"detail": "Only Won leads can be converted."}, status=status.HTTP_400_BAD_REQUEST)
                if lead.converted_client_id:
                    return Response({"detail": "This lead has already been converted."}, status=status.HTTP_409_CONFLICT)

                if existing_client_id:
                    client = Client.objects.filter(pk=existing_client_id).first()
                    if client is None:
                        return Response({"detail": "Client not found."}, status=status.HTTP_404_NOT_FOUND)
                    created_new_client = False
                else:
                    duplicates = self._find_possible_duplicates(lead)
                    if duplicates:
                        return Response(
                            {
                                "code": "POSSIBLE_DUPLICATE_CLIENT",
                                "detail": "A possible matching client already exists. Select it to convert this lead.",
                                "candidates": ClientConversionSerializer(duplicates[:5], many=True).data,
                            },
                            status=status.HTTP_409_CONFLICT,
                        )
                    client = Client.objects.create(
                        display_name=lead.name,
                        company_name=lead.company_name,
                        email=lead.email,
                        phone=lead.phone,
                        created_by=request.user,
                        created_from_lead=lead,
                    )
                    created_new_client = True

                lead.converted_client = client
                lead.converted_at = timezone.now()
                lead.converted_by = request.user
                lead.updated_by = request.user
                lead.save(update_fields=("converted_client", "converted_at", "converted_by", "updated_by", "updated_at"))
                LeadActivity.objects.create(
                    lead=lead,
                    kind=LeadActivity.Kind.CONVERSION,
                    description="Won lead converted to a client.",
                    new_values={"client_id": str(client.id), "created_new_client": created_new_client},
                    actor=request.user,
                )
                record_crm_audit(
                    request.user,
                    AuditEvent.Action.CRM_LEAD_CONVERTED,
                    "crm.lead",
                    lead.id,
                    metadata={"client_id": str(client.id), "created_new_client": created_new_client},
                )
        except IntegrityError:
            return Response({"detail": "This lead was converted concurrently. Refresh the lead before retrying."}, status=status.HTTP_409_CONFLICT)

        return Response(
            {
                "lead_id": str(lead.id),
                "client": ClientConversionSerializer(client).data,
                "created_new_client": created_new_client,
            },
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _find_possible_duplicates(lead):
        matches = Q()
        has_match_key = False
        if lead.email:
            matches |= Q(email__iexact=lead.email)
            has_match_key = True
        if lead.phone:
            matches |= Q(phone=lead.phone)
            has_match_key = True
        if not has_match_key and lead.company_name:
            matches = Q(company_name__iexact=lead.company_name, display_name__iexact=lead.name)
            has_match_key = True
        return Client.objects.filter(matches).order_by("display_name") if has_match_key else Client.objects.none()


class CrmDashboardView(APIView):
    permission_classes = [CanUseCrm]

    def get(self, request):
        leads = scoped_leads(request.user)
        status_counts = {value: leads.filter(status=value).count() for value, _ in Lead.Status.choices}
        summary = {
            "total": leads.count(),
            "by_status": status_counts,
            "follow_ups_due": leads.filter(follow_up_date__lte=timezone.localdate())
            .exclude(status__in=(Lead.Status.WON, Lead.Status.LOST))
            .count(),
        }
        serializer = CrmDashboardSerializer(data=summary)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)