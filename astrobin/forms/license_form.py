from django import forms

from astrobin.models import Image


class ImageLicenseForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('license',)
