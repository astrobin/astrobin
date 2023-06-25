import logging

from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django.contrib.auth.forms import PasswordResetForm as BasePasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.translation import gettext
from djangojs.conf import settings

log = logging.getLogger(__name__)


class PasswordResetForm(BasePasswordResetForm):
    recaptcha = ReCaptchaField(
        label=gettext('Are you a robot?'),
        widget=ReCaptchaV2Checkbox(
            attrs={
                'data-theme': 'dark',
            }
        )
    )

    subject_template_name = 'registration/password_reset_subject.txt'
    email_template_name = 'registration/password_reset_email.txt'
    html_email_template_name = 'registration/password_reset_email.html'
    from_email = settings.DEFAULT_FROM_EMAIL

    def clean_email(self):
        email = self.cleaned_data['email']
        users = self.get_users(email)
        length = len(list(users))

        if length == 0:
            self.add_error(
                'email',
                gettext(
                    'This email address was not found in our database. Email address might be case sensitive.'
                )
            )
        elif length > 1:
            self.add_error(
                'email',
                gettext(
                    'We found more than one account associated with this email address and we cannot proceed with this '
                    'operation. Please get in touch with support to resolve the issue.'
                )
            )

        return email

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
