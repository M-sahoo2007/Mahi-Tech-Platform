from django.urls import path

from . import views

urlpatterns = [
    path("auth/csrf/", views.csrf_token, name="auth-csrf"),
    path("auth/login/", views.login_view, name="auth-login"),
    path("auth/logout/", views.logout_view, name="auth-logout"),
    path("auth/me/", views.current_user, name="auth-me"),
    path("accounts/", views.account_collection, name="account-collection"),
    path("accounts/<uuid:user_id>/", views.account_detail, name="account-detail"),
]