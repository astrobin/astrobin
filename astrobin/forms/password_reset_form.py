import logging

from django.contrib.auth.forms import PasswordResetForm as BasePasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from djangojs.conf import settings

log = logging.getLogger('apps')


class PasswordResetForm(BasePasswordResetForm):
    subject_template_name = 'registration/password_reset_subject.txt'
    email_template_name = 'registration/password_reset_email.txt'
    html_email_template_name = 'registration/password_reset_email.html'
    from_email = settings.DEFAULT_FROM_EMAIL

    def send_mail(
            self,
            subject_template_name,
            email_template_name,
            context,
            from_email,
            to_email,
            html_email_template_name=None
    ):
        super().send_mail(
            subject_template_name,
            email_template_name,
            context,
            from_email,
            settings.EMAIL_DEV_RECIPIENT if settings.SEND_EMAILS == 'dev' else to_email,
            html_email_template_name,
        )

        log.info(f'Password reset email sent to {to_email}')

    def save(
            self,
            domain_override=None,
            subject_template_name='registration/password_reset_subject.txt',
            email_template_name='registration/password_reset_email.txt',
            use_https=False,
            token_generator=default_token_generator,
            from_email=None,
            request=None,
            html_email_template_name='registration/password_reset_email.html',
            extra_email_context=None
    ):
        super().save(
            settings.BASE_URL,
            self.subject_template_name,
            self.email_template_name,
            use_https,
            token_generator,
            self.from_email,
            request,
            self.html_email_template_name,
            extra_email_context,
        )
