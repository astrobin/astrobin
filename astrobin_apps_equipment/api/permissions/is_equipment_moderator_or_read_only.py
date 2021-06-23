from rest_framework import permissions


class IsEquipmentModeratorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.groups.filter(name='equipment_moderators').exists()
