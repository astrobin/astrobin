from django.conf import settings
from django.contrib.auth.models import User


class ModerationService(object):
    @staticmethod
    def auto_enqueue_for_moderation(user: User) -> bool:
        moderate_countries = ['ru', 'cn']
        return hasattr(
            user, 'userprofile'
        ) and user.userprofile.last_seen_in_country and user.userprofile.last_seen_in_country in moderate_countries

    @staticmethod
    def auto_approve(user: User) -> bool:
        for domain in settings.AUTO_APPROVE_DOMAINS:
            if user.email.endswith(domain):
                return True

        if user.groups.filter(name="auto_approve_content").exists():
            return True

        return False
