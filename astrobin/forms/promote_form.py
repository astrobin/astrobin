from django import forms

from astrobin.models import Image


class ImagePromoteForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ()
