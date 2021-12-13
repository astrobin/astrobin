from rest_framework import permissions


class IsIotdReviewer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='iotd_reviewers').exists()
