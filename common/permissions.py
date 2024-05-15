from typing import List, Type, Union

from rest_framework import permissions

from astrobin_apps_users.services import UserService


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        return False


class IsObjectUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsObjectUserOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


def or_permission(*perms):
    class OrPermission(permissions.BasePermission):
        def __init__(self, *perms):
            self.perms = perms

        def has_permission(self, request, view):
            return any(perm().has_permission(request, view) for perm in self.perms)

        def has_object_permission(self, request, view, obj):
            return any(perm().has_object_permission(request, view, obj) for perm in self.perms)

    class CombinedPermission(OrPermission):
        def __init__(self):
            super().__init__(*perms)

    return CombinedPermission


def is_group_member(group_name: Union[str, List[str]]) -> Type[permissions.BasePermission]:
    class _IsGroupMember(permissions.BasePermission):
        def has_permission(self, request, view) -> bool:
            return UserService(request.user).is_in_group(group_name)

    return _IsGroupMember
