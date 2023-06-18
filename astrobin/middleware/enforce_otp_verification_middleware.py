import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.signing import BadSignature, SignatureExpired
from django_otp import devices_for_user
from django_otp.plugins.otp_email.models import EmailDevice
from django_otp.plugins.otp_totp.models import TOTPDevice
from two_factor.views.utils import validate_remember_device_cookie

from astrobin.middleware.mixins import MiddlewareParentClass
from astrobin.utils import get_client_country_code
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_users.services import UserService

log = logging.getLogger(__name__)


class EnforceOtpVerificationMiddleware(MiddlewareParentClass):
    def _is_login_request(self, request):
        return request.path.startswith('/account/login')

    def _is_post(self, request):
        return request.method == 'POST'

    def _process(self, request):
        has_user = hasattr(request, 'user')
        is_authenticated = has_user and request.user.is_authenticated
        is_ajax = request.is_ajax()
        is_api = 'HTTP_AUTHORIZATION' in request.META
        is_localhost = 'localhost' in request.get_host() or '127.0.0.1' in request.get_host()
        return (
                has_user and
                not is_authenticated and
                not is_ajax and
                not is_api and
                not is_localhost and
                self._is_post(request)
        )

    def _create_email_device(self, user):
        return EmailDevice.objects.get_or_create(
            user=user, name="default", confirmed=True
        )

    def _remember_agent(self, request, user, otp_device_id):
        remember = False

        for key, value in request.COOKIES.items():
            if key.startswith(settings.TWO_FACTOR_REMEMBER_COOKIE_PREFIX) and value:
                try:
                    remember = validate_remember_device_cookie(
                        value,
                        user,
                        otp_device_id
                    )
                except (BadSignature, SignatureExpired):
                    return False

        return remember

    def process_request(self, request):
        if not (self._is_login_request(request) and self._is_post(request)):
            return

        handle = request.POST.get('auth-username')
        password = request.POST.get('auth-password')
        user = None

        if not handle:
            log.warning('enforce_otp_verification_middleware: unable to find username in request')
            return

        try:
            user = UserService.get_case_insensitive(handle)
        except User.DoesNotExist:
            log.debug(f'enforce_otp_verification_middleware: user with username {handle} does not exist')

        if not user:
            try:
                user = User.objects.get(email__iexact=handle)
            except User.DoesNotExist:
                log.debug(f'enforce_otp_verification_middleware: user with email {handle} does not exist')
                return
            except User.MultipleObjectsReturned:
                log.debug(f'enforce_otp_verification_middleware: user with email {handle}: multiple found')
                return

        if EmailDevice.objects.filter(user=user).exists():
            request.session['enforce_otp_middleware_email_device'] = 1
        elif TOTPDevice.objects.filter(user=user).exists():
            request.session['enforce_otp_middleware_totp_device'] = 1

        if not self._process(request):
            return

        # Bail if the password is not matching.

        if not user.check_password(password):
            log.debug(f'enforce_otp_verification_middleware: user {handle} used an incorrect password')
            return

        # First check if we remember this device.

        devices = list(devices_for_user(user))
        for device in devices:
            if self._remember_agent(request, user, device.persistent_id):
                log.debug(
                    f'enforce_otp_verification_middleware: user {handle} skips token authentication because we '
                    f'remember this agent'
                )
                return

        # Then check for the country.

        country_code = get_client_country_code(request)
        is_new_country = country_code.lower() != user.userprofile.last_seen_in_country

        if is_new_country or country_code in (None, 'UNKNOWN'):
            log.debug(
                f'enforce_otp_verification_code: user {handle} attempted to log in from new country '
                f'{country_code}'
            )

            device, created = self._create_email_device(user)
            request.session['enforce_otp_middleware_new_country'] = 1

            log.debug(f'enforce_otp_verification_middleware: user {handle} -> email device created = {created}')
            push_notification([user], None, 'access_attempted_from_different_country', {})

            return

        # Then check for the password validity.

        try:
            validate_password(password, user)
            log.debug(f'enforce_otp_verification_middleware: user {handle} used a correct and valid password')
        except ValidationError:
            device, created = self._create_email_device(user)
            request.session['enforce_otp_middleware_invalid_password'] = 1

            log.debug(
                f'enforce_otp_verification_middleware: user {handle} attempted to log in with password {password} '
                f'and it does not meet security standards'
            )

            log.debug(
                f'enforce_otp_verification_middleware: user {handle} -> email device created = {created}'
            )

            push_notification([user], None, 'access_attempted_with_weak_password', {})
