from django import forms

from astrobin.models import GearUserInfo


class GearUserInfoForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = GearUserInfo
        exclude = []
