from datetime import datetime, timedelta

from cookie_consent.util import get_cookie_value_from_request

from astrobin.middleware.mixins import MiddlewareParentClass
from astrobin.models import UserProfile
from astrobin.templatetags.tags import is_gdpr_country
from astrobin.utils import get_client_country_code
from astrobin_apps_users.services import UserService

LAST_SEEN_COOKIE = 'astrobin_last_seen_set'


class LastSeenMiddleware(MiddlewareParentClass):
    def _process(self, request):
        return (
                hasattr(request, 'user') and
                hasattr(request.user, 'userprofile') and
                request.user.is_authenticated and
                not request.is_ajax() and
                not 'HTTP_AUTHORIZATION' in request.META and
                not request.COOKIES.get(LAST_SEEN_COOKIE)
        )

    def process_response(self, request, response):
        if self._process(request):
            country_code = get_client_country_code(request)
            UserService(request.user).set_last_seen(country_code)

            profile = request.user.userprofile

            if country_code is not None and country_code != 'UNKNOWN' and profile.signup_country is None:
                UserProfile.objects.filter(user=request.user).update(signup_country=country_code)

            max_age = 60 * 60
            expires = datetime.strftime(datetime.utcnow() + timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")

            if not is_gdpr_country(request) or get_cookie_value_from_request(request,  'performance'):
                response.set_cookie(LAST_SEEN_COOKIE, 1, max_age=max_age, expires=expires)

        return response
