from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django import forms
from django.utils.translation import ugettext_lazy as _
from threaded_messages.fields import CommaSeparatedUserField
from threaded_messages.forms import ComposeForm


class PrivateMessageForm(ComposeForm):
    recipient = CommaSeparatedUserField(label=_(u'Recipients'), required=True)

    subject = forms.CharField(max_length=255, required=True)

    body = forms.CharField(widget=forms.Textarea, max_length=4096, required=True)


class PrivateMessageFormWithRecaptcha(PrivateMessageForm):
    recaptcha = ReCaptchaField(
        label=_('Are you a robot?'),
        widget=ReCaptchaV2Checkbox(
            attrs={
                'data-theme': 'dark',
            }
        )
    )
