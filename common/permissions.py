from rest_framework import permissions
from rest_framework.permissions import IsAdminUser


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        return False


class IsAdminUserOrReadOnly(IsAdminUser):
    def has_permission(self, request, view):
        is_admin = super(IsAdminUserOrReadOnly,self).has_permission(request, view)
        return request.method in permissions.SAFE_METHODS or is_admin
