from django import forms

from astrobin.models import Image


class ImageFlagThumbsForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ()
