from rest_framework import permissions

from astrobin_apps_users.services import UserService
from common.constants import GroupName


class MayAccessMarketplace(permissions.BasePermission):
    def _has_permission(self, request):
        if request.user.is_superuser:
            return True

        return (
                UserService(request.user).is_in_group(GroupName.MARKETPLACE_MODERATORS) or
                UserService(request.user).is_in_astrobin_group(GroupName.BETA_TESTERS)
        )

    def has_object_permission(self, request, view, obj):
        return self._has_permission(request)

    def has_permission(self, request, view):
        return self._has_permission(request)
