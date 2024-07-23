from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django.forms import forms
from django.utils.translation import gettext


class PasswordChangeRequestTokenForm(forms.Form):
    recaptcha = ReCaptchaField(
        label=gettext('Are you a robot?'),
        widget=ReCaptchaV2Checkbox(
            attrs={
                'data-theme': 'dark',
            }
        )
    )
