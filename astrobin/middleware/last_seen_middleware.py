from datetime import datetime, timedelta

from astrobin.models import UserProfile
from astrobin.utils import get_client_country_code

LAST_SEEN_COOKIE = 'astrobin_last_seen_set'


class LastSeenMiddleware(object):
    def _process(self, request):
        return (
                hasattr(request, 'user') and
                request.user.is_authenticated() and
                not request.is_ajax() and
                not request.COOKIES.get(LAST_SEEN_COOKIE)
        )

    def process_response(self, request, response):
        if self._process(request):
            try:
                profile = UserProfile.objects.get(user=request.user)
                profile.last_seen = datetime.now()

                country_code = get_client_country_code(request)
                if country_code and country_code != 'UNKNOWN':
                    try:
                        profile.last_seen_in_country = country_code.lower()[0:2]
                    except IndexError:
                        pass

                profile.save(keep_deleted=True)

                max_age = 60 * 60
                expires = datetime.strftime(datetime.utcnow() + timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
                response.set_cookie(LAST_SEEN_COOKIE, 1, max_age=max_age, expires=expires)
            except UserProfile.DoesNotExist:
                pass

        return response
