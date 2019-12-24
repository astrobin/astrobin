from django import forms

from astrobin.models import AppApiKeyRequest


class AppApiKeyRequestForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = AppApiKeyRequest
        exclude = []
