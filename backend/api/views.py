from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DashboardSummarySerializer

User = get_user_model()

def health(request):
    return JsonResponse({
        "status": "ok",
        "service": "Mahi-Tech Platform API",
        "message": "Backend is running",
        "timestamp": timezone.now().isoformat(),
    })


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        team_accounts = User.objects.filter(groups__name="Team").distinct()
        user = request.user
        cache_backend = settings.CACHES["default"]["BACKEND"]
        cache_kind = "redis" if cache_backend.endswith("RedisCache") else "local"
        probe_key = f"dashboard-probe:{uuid4()}"
        try:
            cache.set(probe_key, "ok", timeout=5)
            cache_status = "connected" if cache.get(probe_key) == "ok" else "unavailable"
        except Exception:
            cache_status = "unavailable"
        finally:
            try:
                cache.delete(probe_key)
            except Exception:
                pass

        summary = {
            "current_user": {
                "id": user.pk,
                "email": user.email,
                "role": "admin" if user.is_superuser or user.has_perm("accounts.manage_users") else "team",
            },
            "team_accounts": {
                "total": team_accounts.count(),
                "active": team_accounts.filter(is_active=True).count(),
            },
            "system": {
                "api": "connected",
                "cache": cache_status,
                "cache_backend": cache_kind,
            },
        }
        serializer = DashboardSummarySerializer(data=summary)
        serializer.is_valid(raise_exception=True)
        return Response({"data": serializer.validated_data})
