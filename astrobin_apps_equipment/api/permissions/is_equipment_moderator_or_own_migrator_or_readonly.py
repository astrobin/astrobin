from rest_framework import permissions


class IsEquipmentModeratorOrOwnMigratorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.groups.filter(name__in=['equipment_moderators', 'own_equipment_migrators']).exists()
