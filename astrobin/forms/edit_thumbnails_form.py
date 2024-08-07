from django import forms

from astrobin.models import Image
from astrobin.widgets.hidden_image_crop_widget import HiddenImageCropWidget


class ImageEditThumbnailsForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Image
        fields = ('image_file', 'square_cropping', 'sharpen_thumbnails')
        widgets = {
            'image_file': HiddenImageCropWidget
        }
