from django.urls import path
from .views import DashboardSummaryView, health

urlpatterns = [
    path("health/", health, name="api-health"),
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
]
