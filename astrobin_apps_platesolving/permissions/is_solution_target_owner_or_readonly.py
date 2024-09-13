from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSolutionTargetOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        target = obj.content_object
        if target.__class__.__name__ == 'Image':
            return target.user == request.user
        else:
            return target.image.user == request.user

        return False
