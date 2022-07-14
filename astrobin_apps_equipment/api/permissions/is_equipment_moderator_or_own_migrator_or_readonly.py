from rest_framework import permissions

from astrobin_apps_users.services import UserService
from common.constants import GroupName


class IsEquipmentModeratorOrOwnMigratorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return UserService(request.user).is_in_group(
            [GroupName.EQUIPMENT_MODERATORS, GroupName.OWN_EQUIPMENT_MIGRATORS]
        )
