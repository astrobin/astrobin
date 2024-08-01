from typing import List, Type, Union

from rest_framework import permissions

from astrobin.templatetags.tags import has_subscription_by_name
from astrobin_apps_users.services import UserService


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


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


def subscription_required(subscription_names: Union[str, List[str]]) -> Type[permissions.BasePermission]:
    class _SubscriptionRequired(permissions.BasePermission):
        def has_permission(self, request, view) -> bool:
            # Loop all subscription_name and return True if user has any of them
            return any(
                has_subscription_by_name(request.user, subscription_name) for subscription_name in subscription_names
            )

    return _SubscriptionRequired
