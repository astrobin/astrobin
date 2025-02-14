from django import forms
from django.conf import settings
from django.utils.translation import gettext

from common.captcha.turnstile_widget import TurnstileWidget


class TurnstileField(forms.CharField):
    widget = TurnstileWidget
    default_error_messages = {
        'required': 'Please complete the CAPTCHA',
        'invalid': 'Invalid CAPTCHA response'
    }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', gettext('Are you a robot?'))
        super().__init__(*args, **kwargs)

    def clean(self, value):
        if not value:
            if settings.DEBUG and settings.TURNSTILE_SITE_KEY == settings.TURNSTILE_TEST_SITE_KEY:
                # In test mode with test key, bypass validation
                return value
            raise forms.ValidationError(self.error_messages['required'])

        import requests
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify', data={
                'secret': settings.TURNSTILE_SECRET_KEY,
                'response': value,
            }
        )

        if not response.json().get('success'):
            if settings.DEBUG and settings.TURNSTILE_SITE_KEY == settings.TURNSTILE_TEST_SITE_KEY:
                # In test mode with test key, bypass validation
                return value
            raise forms.ValidationError(self.error_messages['invalid'])

        return value
