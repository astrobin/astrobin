import logging

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_otp.plugins.otp_email.models import EmailDevice
from django_otp.plugins.otp_totp.models import TOTPDevice

from astrobin.fields import get_country_name
from astrobin.middleware.mixins import MiddlewareParentClass
from astrobin.models import UserProfile
from astrobin.services.utils_service import UtilsService
from astrobin.utils import get_client_country_code
from astrobin_apps_notifications.services.notifications_service import NotificationContext
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_users.services import UserService

log = logging.getLogger(__name__)


class LoginAttemptMiddleware(MiddlewareParentClass):
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

    def process_request(self, request):
        if not (self._is_login_request(request) and self._is_post(request)):
            return

        handle = request.POST.get('auth-username')
        password = request.POST.get('auth-password')
        user = None

        if not handle:
            log.warning('login_attempt_middleware: unable to find username in request')
            return

        try:
            user = UserService.get_case_insensitive(handle)
        except User.DoesNotExist:
            log.debug(f'login_attempt_middleware: user with username {handle} does not exist')
        except ValueError:
            log.debug(f'login_attempt_middleware: user with username {handle}: ValueError')
            return

        if not user:
            try:
                user = User.objects.get(email__iexact=handle)
            except User.DoesNotExist:
                log.debug(f'login_attempt_middleware: user with email {handle} does not exist')
                return
            except User.MultipleObjectsReturned:
                log.debug(f'login_attempt_middleware: user with email {handle}: multiple found')
                return

        if EmailDevice.objects.filter(user=user).exists():
            request.session['login_attempt_middleware_email_device'] = 1
            request.session['login_attempt_middleware_user_email'] = UtilsService.anonymize_email(user.email)
        elif TOTPDevice.objects.filter(user=user).exists():
            request.session['login_attempt_middleware_totp_device'] = 1

        if not self._process(request):
            return

        # Bail if the password is not matching.
        if not user.check_password(password):
            log.debug(f'login_attempt_middleware: user {handle} used an incorrect password')
            return

        # Check for the country.
        country_code = get_client_country_code(request)
        is_new_country = country_code.lower() != user.userprofile.last_seen_in_country

        if is_new_country or country_code in (None, 'UNKNOWN'):
            log.debug(
                f'enforce_otp_verification_code: user {handle} attempted to log in from new country '
                f'{country_code}'
            )
            push_notification(
                [user],
                None,
                'access_attempted_from_different_country',
                {
                    'last_seen_in_country': get_country_name(user.userprofile.last_seen_in_country.upper())
                    if user.userprofile.last_seen_in_country
                    else 'UNKNOWN',
                    'new_country': get_country_name(country_code.upper()) if country_code else 'UNKNOWN',
                    'ip': request.META.get('REMOTE_ADDR'),
                    'extra_tags': {
                        'context': NotificationContext.AUTHENTICATION
                    },
                }
            )

        # Check for the password validity.
        try:
            validate_password(password, user)
            log.debug(f'login_attempt_middleware: user {handle} used a correct and valid password')
        except ValidationError:
            UserProfile.objects.filter(user=user).update(
                detected_insecure_password=timezone.now(),
            )

            if not user.userprofile.password_reset_token:
                password_reset_token = User.objects.make_random_password(32)
                UserProfile.objects.filter(user=user).update(
                    password_reset_token=password_reset_token
                )
            else:
                password_reset_token = user.userprofile.password_reset_token

            log.debug(
                f'login_attempt_middleware: user {handle} attempted to log in with password {password} '
                f'and it does not meet security standards'
            )

            push_notification(
                [user],
                None,
                'access_attempted_with_weak_password', {
                    'token': password_reset_token,
                    'extra_tags': {
                        'context': NotificationContext.AUTHENTICATION
                    },
                })
