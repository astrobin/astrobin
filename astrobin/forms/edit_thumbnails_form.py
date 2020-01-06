from django import forms
from image_cropping import ImageCropWidget

from astrobin.models import Image


class ImageEditThumbnailsForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Image
        fields = ('image_file', 'square_cropping')
        widgets = {
            'image_file': ImageCropWidget
        }
