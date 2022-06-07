from rest_framework import throttling

from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free


class EquipmentCreateThrottle(throttling.UserRateThrottle):
    rate = '10/day'

    def allow_request(self, request, view):
        if request.method != "POST":
            return True

        if request.user.is_superuser:
            return True

        valid_subscription = PremiumService(request.user).get_valid_usersubscription()
        if not is_free(valid_subscription):
            return True

        return super().allow_request(request, view)
