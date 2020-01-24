from django import forms

from astrobin.models import Image
from astrobin.widgets import HiddenImageCropWidget


class ImageEditThumbnailsForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Image
        fields = ('image_file', 'square_cropping')
        widgets = {
            'image_file': HiddenImageCropWidget
        }
