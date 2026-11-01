from django.http import JsonResponse
from django.utils import timezone

def health(request):
    return JsonResponse({
        "status": "ok",
        "service": "Mahi-Tech Platform API",
        "message": "Backend is running",
        "timestamp": timezone.now().isoformat(),
    })
