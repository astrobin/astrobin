from django import forms

from astrobin.models import Image


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('image_file', 'skip_notifications')
