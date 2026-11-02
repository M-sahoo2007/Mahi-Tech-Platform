import hashlib
import hmac
import json

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import AuditEvent, normalize_email

User = get_user_model()
ROLE_NAMES = {"admin": "Admin", "team": "Team"}


def _json_body(request):
    if request.content_type != "application/json":
        return None, JsonResponse({"detail": "Content-Type must be application/json."}, status=415)
    try:
        payload = json.loads(request.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = None
    if not isinstance(payload, dict):
        return None, JsonResponse({"detail": "A valid JSON object is required."}, status=400)
    return payload, None


def _is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.has_perm("accounts.manage_users"))


def _user_payload(user):
    role = "admin" if user.is_superuser or user.groups.filter(name=ROLE_NAMES["admin"]).exists() else "team"
    return {
        "id": str(user.pk),
        "email": user.email,
        "is_active": user.is_active,
        "role": role,
    }


def _role_group(role):
    group, _ = Group.objects.get_or_create(name=ROLE_NAMES[role])
    manage_permission = Permission.objects.get(
        content_type__app_label="accounts",
        codename="manage_users",
    )
    if role == "admin":
        group.permissions.add(manage_permission)
    else:
        group.permissions.remove(manage_permission)
    return group


def _admin_denial(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    if not _is_admin(request.user):
        _record_audit(request.user, AuditEvent.Action.ACCESS_DENIED)
        return JsonResponse({"detail": "Administrator permission required."}, status=403)
    return None


def _other_active_admin_exists(excluded_user):
    active_users = User.objects.filter(is_active=True).exclude(pk=excluded_user.pk)
    return active_users.filter(is_superuser=True).exists() or active_users.filter(
        groups__permissions__content_type__app_label="accounts",
        groups__permissions__codename="manage_users",
    ).exists()


def _login_cache_keys(email, request):
    client_ip = request.META.get("REMOTE_ADDR", "unknown")
    identity_digest = hmac.new(settings.SECRET_KEY.encode(), email.encode(), hashlib.sha256).hexdigest()
    address_digest = hmac.new(settings.SECRET_KEY.encode(), client_ip.encode(), hashlib.sha256).hexdigest()
    return (f"auth-login:email:{identity_digest}", f"auth-login:ip:{address_digest}")


def _record_audit(actor, action, target_user=None, metadata=None):
    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        target_user=target_user,
        metadata=metadata or {},
    )


@require_GET
@ensure_csrf_cookie
def csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


@require_POST
@csrf_protect
def login_view(request):
    payload, error = _json_body(request)
    if error:
        return error

    email = payload.get("email")
    password = payload.get("password")
    if not isinstance(email, str) or not email.strip() or not isinstance(password, str) or not password:
        return JsonResponse({"detail": "Email and password are required."}, status=400)

    normalized_email = normalize_email(email)
    throttle_keys = _login_cache_keys(normalized_email, request)
    try:
        if any(cache.get(key, 0) >= settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS for key in throttle_keys):
            return JsonResponse(
                {"detail": "Unable to sign in right now. Please try again later."},
                status=429,
                headers={"Retry-After": str(settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)},
            )
    except Exception:
        return JsonResponse({"detail": "Sign-in is temporarily unavailable."}, status=503)

    user = authenticate(request, email=normalized_email, password=password)
    if user is None:
        try:
            for key in throttle_keys:
                if not cache.add(key, 1, timeout=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS):
                    try:
                        cache.incr(key)
                    except ValueError:
                        if not cache.add(key, 1, timeout=settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS):
                            cache.incr(key)
        except Exception:
            return JsonResponse({"detail": "Sign-in is temporarily unavailable."}, status=503)
        return JsonResponse({"detail": "Invalid email or password."}, status=401)

    try:
        cache.delete_many(throttle_keys)
    except Exception:
        return JsonResponse({"detail": "Sign-in is temporarily unavailable."}, status=503)

    login(request, user)
    return JsonResponse({"user": _user_payload(user)})


@require_POST
@csrf_protect
def logout_view(request):
    logout(request)
    return JsonResponse({"detail": "Signed out."})


@require_GET
def current_user(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    return JsonResponse({"user": _user_payload(request.user)})


@require_http_methods(["GET", "POST"])
@csrf_protect
def account_collection(request):
    denial = _admin_denial(request)
    if denial:
        return denial

    if request.method == "GET":
        with transaction.atomic():
            _record_audit(request.user, AuditEvent.Action.ACCOUNT_LISTED)
            users = User.objects.order_by("email")
        return JsonResponse({"accounts": [_user_payload(user) for user in users]})

    payload, error = _json_body(request)
    if error:
        return error
    if set(payload) != {"email", "password", "role"}:
        return JsonResponse({"detail": "Email, password, and role are required."}, status=400)

    email = payload["email"]
    password = payload["password"]
    role = payload["role"]
    if not isinstance(email, str) or not email.strip():
        return JsonResponse({"detail": "A valid email address is required."}, status=400)
    if not isinstance(password, str) or not password:
        return JsonResponse({"detail": "A password is required."}, status=400)
    if not isinstance(role, str) or role not in ROLE_NAMES:
        return JsonResponse({"detail": "Role must be admin or team."}, status=400)

    email = normalize_email(email)
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({"detail": "A valid email address is required."}, status=400)
    if User.objects.filter(email=email).exists():
        return JsonResponse({"detail": "An account with this email already exists."}, status=409)

    user_for_validation = User(email=email)
    try:
        validate_password(password, user=user_for_validation)
    except ValidationError as validation_error:
        return JsonResponse({"detail": "Password does not meet the configured requirements.", "password": validation_error.messages}, status=400)

    with transaction.atomic():
        user = User.objects.create_user(email=email, password=password)
        user.groups.set([_role_group(role)])
        _record_audit(
            request.user,
            AuditEvent.Action.ACCOUNT_CREATED,
            target_user=user,
            metadata={"role": role},
        )
    return JsonResponse({"user": _user_payload(user)}, status=201)


@require_http_methods(["PATCH"])
@csrf_protect
def account_detail(request, user_id):
    denial = _admin_denial(request)
    if denial:
        return denial

    payload, error = _json_body(request)
    if error:
        return error
    if not payload or not set(payload).issubset({"is_active", "role"}):
        return JsonResponse({"detail": "Only is_active and role may be updated."}, status=400)

    user = User.objects.filter(pk=user_id).first()
    if user is None:
        return JsonResponse({"detail": "Account not found."}, status=404)

    requested_active = payload.get("is_active", user.is_active)
    requested_role = payload.get("role", _user_payload(user)["role"])
    if not isinstance(requested_active, bool):
        return JsonResponse({"detail": "is_active must be a boolean."}, status=400)
    if not isinstance(requested_role, str) or requested_role not in ROLE_NAMES:
        return JsonResponse({"detail": "Role must be admin or team."}, status=400)
    if user.is_superuser and requested_role != "admin":
        return JsonResponse({"detail": "Superuser role cannot be changed here."}, status=400)
    if user.pk == request.user.pk and (not requested_active or requested_role != "admin"):
        return JsonResponse({"detail": "You cannot deactivate or demote your own account."}, status=400)

    previous_active = user.is_active
    previous_role = _user_payload(user)["role"]
    was_admin = _is_admin(user)
    will_be_admin = user.is_superuser or requested_role == "admin"
    if was_admin and (not requested_active or not will_be_admin) and not _other_active_admin_exists(user):
        return JsonResponse({"detail": "At least one active administrator must remain."}, status=400)

    with transaction.atomic():
        user.is_active = requested_active
        user.groups.set([_role_group(requested_role)])
        user.save(update_fields=["is_active"])
        if previous_active != requested_active:
            action = AuditEvent.Action.ACCOUNT_ACTIVATED if requested_active else AuditEvent.Action.ACCOUNT_DEACTIVATED
            _record_audit(request.user, action, target_user=user)
        if previous_role != requested_role:
            _record_audit(
                request.user,
                AuditEvent.Action.ROLE_ASSIGNED,
                target_user=user,
                metadata={"previous_role": previous_role, "role": requested_role},
            )
    return JsonResponse({"user": _user_payload(user)})