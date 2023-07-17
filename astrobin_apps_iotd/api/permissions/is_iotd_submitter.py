from rest_framework import permissions

from astrobin_apps_users.services import UserService
from common.constants import GroupName


class IsIotdSubmitter(permissions.BasePermission):
    def has_permission(self, request, view):
        return UserService(request.user).is_in_group(GroupName.IOTD_SUBMITTERS)
