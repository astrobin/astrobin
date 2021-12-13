from rest_framework import permissions


class IsIotdJudge(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='iotd_judges').exists()
