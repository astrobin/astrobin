from django.conf import settings
from django.contrib.auth.models import User


class ModerationService(object):
    @staticmethod
    def auto_approve(user: User) -> bool:
        for domain in settings.AUTO_APPROVE_DOMAINS:
            if user.email.endswith(domain):
                return True

        return False
