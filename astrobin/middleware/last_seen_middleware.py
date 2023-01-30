from datetime import datetime, timedelta

from astrobin.middleware.mixins import MiddlewareParentClass
from astrobin.utils import get_client_country_code
from astrobin_apps_users.services import UserService

LAST_SEEN_COOKIE = 'astrobin_last_seen_set'


class LastSeenMiddleware(MiddlewareParentClass):
    def _process(self, request):
        return (
                hasattr(request, 'user') and
                request.user.is_authenticated and
                not request.is_ajax() and
                not 'HTTP_AUTHORIZATION' in request.META and
                not request.COOKIES.get(LAST_SEEN_COOKIE)
        )

    def process_response(self, request, response):
        if self._process(request):
            country_code = get_client_country_code(request)
            UserService(request.user).set_last_seen(country_code)
            max_age = 60 * 60
            expires = datetime.strftime(datetime.utcnow() + timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
            response.set_cookie(LAST_SEEN_COOKIE, 1, max_age=max_age, expires=expires)

        return response
