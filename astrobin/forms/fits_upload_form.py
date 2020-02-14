from django import forms

from astrobin.models import Image


class ImageFitsUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('fits_file',)
