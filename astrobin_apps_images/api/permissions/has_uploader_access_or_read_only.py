from rest_framework import permissions

from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_any_ultimate, is_premium


class HasUploaderAccessOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return is_any_ultimate(request.user) or is_premium(request.user)
