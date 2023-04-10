import logging

from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext
from djcelery_email.backends import CeleryEmailBackend
from djcelery_email.tasks import send_emails

log = logging.getLogger('apps')


class CustomCeleryEmailBackend(CeleryEmailBackend):
    """
    A wrapper around the Celery backend that:
      - doesn't use Celery for priority emails
    """

    def send_messages(self, email_messages):
        # We send without Celery if any of the email messages matches any of the priority subjects in any language.

        send_via_celery = True

        priority_subjects = [
            'Your AstroBin authentication token'
        ]

        for email_message in email_messages:
            subject = str(email_message.subject)
            for priority_subject in priority_subjects:
                for language in settings.LANGUAGES:
                    with translation.override(language[0]):
                        localized_subject = gettext(priority_subject)
                        if subject == localized_subject:
                            send_via_celery = False

        if send_via_celery:
            return super().send_messages(email_messages)

        log.debug("Sending emails via priority thread.")
        send_emails(email_messages)
