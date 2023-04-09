import logging

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend

log = logging.getLogger('apps')


class LoggingEmailBackend(EmailBackend):
    """
    A wrapper around the SMTP backend that logs all emails.
    """

    def send_messages(self, email_messages):
        if settings.SEND_EMAILS == 'dev':
            for email in email_messages:
                email.to = [settings.EMAIL_DEV_RECIPIENT]
                email.cc = []
                email.bcc = []

        recipients = []
        subjects = []
        for email_message in email_messages:
            recipients.append(','.join(email_message.recipients()))
            subjects.append(email_message.subject)

        recipients_str = ",".join(set(recipients))
        subjects_str = ",".join([str(x) for x in set(subjects)])

        log.info(f'Sending email to {recipients_str}: {subjects_str}')

        try:
            return super().send_messages(email_messages)
        except Exception as e:
            log.error(f'Exception sending email to {recipients_str}: {subjects_str}: {str(e)}')
