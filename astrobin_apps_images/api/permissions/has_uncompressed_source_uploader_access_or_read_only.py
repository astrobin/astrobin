from rest_framework import permissions

from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_any_ultimate


class HasUncompressedSourceUploaderAccessOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        valid_subscription = PremiumService(request.user).get_valid_usersubscription()

        return is_any_ultimate(valid_subscription)
