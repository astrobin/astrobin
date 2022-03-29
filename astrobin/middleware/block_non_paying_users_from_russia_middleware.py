from django.http import HttpResponseBadRequest
from django.shortcuts import redirect

from astrobin.middleware.mixins import MiddlewareParentClass
from astrobin.utils import get_client_country_code
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free


class BlockNonPayingUsersFromRussiaMiddleware(MiddlewareParentClass):
    def _process(self, request):
        country_code = get_client_country_code(request)

        return (
                hasattr(request, 'user') and
                country_code.lower() == 'ru' and
                not request.path.startswith('/accounts/') and
                (
                        not request.user.is_authenticated or
                        is_free(PremiumService(request.user).get_valid_usersubscription())
                )
        )

    def process_response(self, request, response):
        if self._process(request):
            url: str = 'https://welcome.astrobin.com/astrobin-stands-with-ukraine'

            if 'HTTP_AUTHORIZATION' in request.META:
                return HttpResponseBadRequest(f'AstroBin stands with Ukraine. Please see {url}')

            return redirect(url)

        return response
