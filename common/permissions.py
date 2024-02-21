from typing import List, Type, Union

from rest_framework import permissions

from astrobin_apps_users.services import UserService


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        return False


class IsObjectUserOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


def is_group_member(group_name: Union[str, List[str]]) -> Type[permissions.BasePermission]:
    class _IsGroupMember(permissions.BasePermission):
        def has_permission(self, request, view) -> bool:
            return UserService(request.user).is_in_group(group_name)

    return _IsGroupMember
