from django import forms

from astrobin.models import ImageRevision


class ImageEditCorruptedRevisionForm(forms.ModelForm):
    class Meta:
        model = ImageRevision
        fields = ('image_file', 'description', )
