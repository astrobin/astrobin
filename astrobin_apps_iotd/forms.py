# Django
from django import forms

# This app
from astrobin_apps_iotd.models import *


class IotdSubmissionCreateForm(forms.ModelForm):
    class Meta:
        model = IotdSubmission
