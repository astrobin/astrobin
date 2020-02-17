from django import forms

from astrobin_apps_iotd.models import IotdSubmission


class IotdSubmissionCreateForm(forms.ModelForm):
    class Meta:
        model = IotdSubmission
        fields = ('image',)
