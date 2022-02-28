from django.conf import settings
from rest_framework import permissions

from astrobin.models import ImageRevision
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import (
    is_any_ultimate, is_premium, is_lite, is_premium_2020, is_lite_2020)


class HasRevisionUploaderAccessOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: ImageRevision) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True

        valid_subscription = PremiumService(request.user).get_valid_usersubscription()

        if is_any_ultimate(valid_subscription) or is_premium(valid_subscription) or is_lite(valid_subscription):
            return True

        revision_count: int = obj.image.revisions.count()

        if is_premium_2020(valid_subscription):
            return revision_count < settings.PREMIUM_MAX_REVISIONS_PREMIUM_2020

        if is_lite_2020(valid_subscription):
            return revision_count < settings.PREMIUM_MAX_REVISIONS_LITE_2020

        return revision_count < settings.PREMIUM_MAX_REVISIONS_FREE_2020
