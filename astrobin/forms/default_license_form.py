from django import forms

from astrobin.models import UserProfile


class DefaultImageLicenseForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('default_license',)
