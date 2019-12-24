from django import forms

from astrobin.models import Image


class ImageDemoteForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ()
