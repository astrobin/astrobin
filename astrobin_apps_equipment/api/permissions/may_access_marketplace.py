from rest_framework import permissions


class MayAccessMarketplace(permissions.BasePermission):
    def _has_permission(self, request):
        return True

    def has_object_permission(self, request, view, obj):
        return self._has_permission(request)

    def has_permission(self, request, view):
        return self._has_permission(request)
