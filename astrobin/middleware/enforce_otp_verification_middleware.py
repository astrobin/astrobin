from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django_otp.plugins.otp_email.models import EmailDevice

from astrobin.middleware.mixins import MiddlewareParentClass
from astrobin.utils import get_client_country_code
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_users.services import UserService


class EnforceOtpVerificationMiddleware(MiddlewareParentClass):
    def _process(self, request):
        has_user = hasattr(request, 'user')
        is_authenticated = has_user and request.user.is_authenticated
        is_ajax = request.is_ajax()
        is_api = 'HTTP_AUTHORIZATION' in request.META
        is_login_request = request.path.startswith('/account/login')
        is_post = request.method == 'POST'
        is_localhost = 'localhost' in request.get_host() or '127.0.0.1' in request.get_host()

        return (
                has_user and
                not is_authenticated and
                not is_ajax and
                not is_api and
                is_login_request and
                is_post and
                not is_localhost
        )

    def _create_email_device(self, user):
        return EmailDevice.objects.get_or_create(
            user=user, name="default", confirmed=True
        )

    def process_request(self, request):
        if not self._process(request):
            return

        username = request.POST.get('auth-username')
        password = request.POST.get('auth-password')

        if not username:
            return

        try:
            user = UserService.get_case_insensitive(username)
            country_code = get_client_country_code(request)
            is_new_country = country_code.lower() != user.userprofile.last_seen_in_country

            if is_new_country or country_code in (None, 'UNKNOWN'):
                device, created = self._create_email_device(user)

                if created:
                    push_notification([user], None, 'access_attempted_from_different_country', {})
            else:
                try:
                    validate_password(password, user)
                except ValidationError as e:
                    device, created = self._create_email_device(user)

                    if created:
                        push_notification([user], None, 'access_attempted_with_weak_password', {})
        except User.DoesNotExist:
            pass
