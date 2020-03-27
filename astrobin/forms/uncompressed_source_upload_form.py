from django import forms

from astrobin.models import Image


class UncompressedSourceUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('uncompressed_source_file',)
