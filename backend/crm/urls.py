from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.CrmDashboardView.as_view(), name="crm-dashboard"),
    path("lead-sources/", views.LeadSourceListCreateView.as_view(), name="lead-source-list"),
    path("lead-sources/<uuid:source_id>/", views.LeadSourceDetailView.as_view(), name="lead-source-detail"),
    path("leads/", views.LeadListCreateView.as_view(), name="lead-list"),
    path("leads/<uuid:lead_id>/", views.LeadDetailView.as_view(), name="lead-detail"),
    path("leads/<uuid:lead_id>/archive/", views.LeadArchiveView.as_view(), name="lead-archive"),
    path("leads/<uuid:lead_id>/activities/", views.LeadActivityListCreateView.as_view(), name="lead-activity-list"),
    path("leads/<uuid:lead_id>/convert/", views.LeadConversionView.as_view(), name="lead-convert"),
]