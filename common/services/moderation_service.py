from django.conf import settings
from django.contrib.auth.models import User
from django_otp.plugins.otp_email.models import EmailDevice
from django_otp.plugins.otp_totp.models import TOTPDevice

from astrobin_apps_users.services import UserService



class ModerationService(object):
    @staticmethod
    def auto_enqueue_for_moderation(user: User) -> bool:
        if not hasattr(user, 'userprofile'):
            return True

        moderate_because_of_country = (
                user.userprofile.last_seen_in_country and
                user.userprofile.last_seen_in_country.lower() in ['ru']
        )

        moderate_because_of_weak_password = (
            user.userprofile.detected_insecure_password and
            not EmailDevice.objects.filter(user=user).exists() and
            not TOTPDevice.objects.filter(user=user).exists()
        )

        return (
            moderate_because_of_country or
            moderate_because_of_weak_password
        )

    @staticmethod
    def auto_approve(user: User) -> bool:
        if user.is_superuser:
            return True

        for domain in settings.AUTO_APPROVE_DOMAINS:
            if user.email.endswith(domain):
                return True

        if UserService(user).is_in_group('auto_approve_content'):
            return True

        return False
