from rest_framework.permissions import BasePermission


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.has_perm("accounts.manage_users"))


def is_team_member(user):
    return user.is_authenticated and user.groups.filter(name="Team").exists()


class CanUseCrm(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user) or is_team_member(request.user)


class IsCrmAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)