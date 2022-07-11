from rest_framework import permissions

from astrobin_apps_users.services import UserService


class IsIotdSubmitter(permissions.BasePermission):
    def has_permission(self, request, view):
        return UserService(request.user).is_in_group('iotd_submitters')
