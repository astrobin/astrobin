from django.conf import settings
from django.contrib.auth.models import User

from astrobin_apps_users.services import UserService


class ModerationService(object):
    @staticmethod
    def auto_enqueue_for_moderation(user: User) -> bool:
        moderate_countries = ['ru']
        return (
                hasattr(user, 'userprofile') and
                user.userprofile.last_seen_in_country and
                user.userprofile.last_seen_in_country.lower() in moderate_countries
        )

    @staticmethod
    def auto_approve(user: User) -> bool:
        for domain in settings.AUTO_APPROVE_DOMAINS:
            if user.email.endswith(domain):
                return True

        if UserService(user).is_in_group('auto_approve_content'):
            return True

        return False
