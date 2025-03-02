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
        kwargs.setdefault('label', gettext('Are you human?'))
        super().__init__(*args, **kwargs)

    def clean(self, value):
        if settings.DEBUG or getattr(settings, 'TESTING', False):
            return value  # Skip validation in test/debug mode

        if not value:
            raise forms.ValidationError(self.error_messages['required'])

        import requests
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify', data={
                'secret': settings.TURNSTILE_SECRET_KEY,
                'response': value,
            }
        )

        if not response.json().get('success'):
            raise forms.ValidationError(self.error_messages['invalid'])

        return value
