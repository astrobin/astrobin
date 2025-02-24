import logging

from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle

from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free

logger = logging.getLogger(__name__)


# See MULTI_THROTTLE_RATES in astrobin/settings/components/rest.py
class MultiRateThrottle(SimpleRateThrottle):
    scope = 'multi'  # dummy scope

    def __init__(self):
        super().__init__()
        self.now = None
        self.history = []  # satisfy DRF

    def get_rate(self) -> str:
        # Return a dummy rate to bypass DRF's configuration check.
        return "1/1"

    def get_ident(self, request):
        return request.user.pk if request.user.is_authenticated else super().get_ident(request)

    def get_request_type(self, request) -> str:
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return 'read'
        return 'write'

    def get_user_tier(self, request) -> str:
        """Return 'premium', 'user', or 'anon' based on request and subscription."""
        if request.user.is_authenticated:
            valid_subscription = PremiumService(request.user).get_valid_usersubscription()
            if not is_free(valid_subscription):
                return 'premium'
            return 'user'
        return 'anon'

    def allow_request(self, request, view) -> bool:
        ident = self.get_ident(request)
        self.now = self.timer()

        tier = self.get_user_tier(request)
        request_type = self.get_request_type(request)

        # Allow view-level override of throttle rates.
        if hasattr(view, 'throttle_rates'):
            tier_rates = view.throttle_rates.get(tier, {})
        else:
            tier_rates = settings.MULTI_THROTTLE_RATES.get(tier, {})

        limits = tier_rates.get(request_type, [])
        for rate in limits:
            num_requests, duration = self.parse_rate(rate)
            cache_key = self.cache_format % {
                'scope': rate,
                'ident': ident
            }
            local_history = self.cache.get(cache_key, [])
            local_history = [timestamp for timestamp in local_history if timestamp > self.now - duration]
            if len(local_history) >= num_requests:
                logger.warning(
                    "Rate limit exceeded: ident=%s, tier=%s, request_type=%s, rate=%s, method=%s, view=%s, time=%s",
                    ident,
                    tier,
                    request_type,
                    rate,
                    request.method,
                    view.__class__.__name__,
                    self.now
                )
                return False

            local_history.append(self.now)
            self.cache.set(cache_key, local_history, duration)

        return True

    def parse_rate(self, rate) -> tuple:
        num, period = rate.split('/')
        num_requests = int(num)

        if period == 'min':
            duration = 60
        elif period.endswith('min'):
            duration = int(period[:-3]) * 60
        elif period == 's':
            duration = 1
        elif period.endswith('s'):
            duration = int(period[:-1])
        elif period == 'hour':
            duration = 3600
        elif period.endswith('hour'):
            duration = int(period[:-4]) * 3600
        else:
            duration = 60

        return num_requests, duration
