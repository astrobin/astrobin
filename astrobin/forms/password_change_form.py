from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm

from common.captcha import TurnstileField


class PasswordChangeForm(BasePasswordChangeForm):
    captcha = TurnstileField()
