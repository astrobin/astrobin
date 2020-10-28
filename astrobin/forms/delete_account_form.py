from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from astrobin.models import UserProfile


class DeleteAccountForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('delete_reason', 'delete_reason_other',)

    def clean(self):
        delete_reason = self.cleaned_data.get('delete_reason')
        delete_reason_other = self.cleaned_data.get('delete_reason_other') or ''

        if delete_reason == UserProfile.DELETE_REASON_OTHER and len(delete_reason_other) < 30:
            message = 'Please tell us why you are deleting your account (minimum 30 characters). Thanks!'
            raise ValidationError(_(message))

        return self.cleaned_data
