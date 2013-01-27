from rest_framework import permissions

class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view, obj=None):
        # Skip the check unless this is an object-level test
        if obj is None:
            return True

        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:            
            return True

        return False
