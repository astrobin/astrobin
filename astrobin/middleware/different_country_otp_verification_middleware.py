from django.contrib.auth.models import User
from django_otp.plugins.otp_email.models import EmailDevice

from astrobin.middleware.mixins import MiddlewareParentClass
from astrobin.utils import get_client_country_code
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_users.services import UserService


class DifferentCountryOtpVerificationMiddleware(MiddlewareParentClass):
    def _process(self, request):
        has_user = hasattr(request, 'user')
        is_authenticated = has_user and request.user.is_authenticated
        is_ajax = request.is_ajax()
        is_api = 'HTTP_AUTHORIZATION' in request.META
        is_login_request = request.path.startswith('/account/login')
        is_post = request.method == 'POST'

        return (
                has_user and
                not is_authenticated and
                not is_ajax and
                not is_api and
                is_login_request and
                is_post
        )

    def process_request(self, request):
        if not self._process(request):
            return

        username = request.POST.get('auth-username')

        try:
            user = UserService.get_case_insensitive(username)
            country_code = get_client_country_code(request)
            is_new_country = country_code != user.userprofile.last_seen_in_country

            if is_new_country or country_code in (None, 'UNKNOWN'):
                device, created = EmailDevice.objects.get_or_create(
                    user=user, name="default", confirmed=True
                )

                if created:
                    push_notification([user], None, 'access_attempted_from_different_country', {})

        except User.DoesNotExist:
            pass
