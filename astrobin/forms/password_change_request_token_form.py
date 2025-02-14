from django.forms import forms

from common.captcha import TurnstileField


class PasswordChangeRequestTokenForm(forms.Form):
    captcha = TurnstileField()

