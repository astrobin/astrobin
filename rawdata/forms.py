# Django
from django.form import ModelForm

# This app
from .models import RawImage

class RawImageUploadForm(ModelForm):
    class Meta:
        model = RawImage
        fields = ('file',)
