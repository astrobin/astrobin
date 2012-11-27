# Python
import os

# Django
from django.forms import ModelForm, ValidationError
from django.utils.translation import ugettext_lazy as _

# This app
from .models import RawImage
from .utils import supported_raw_formats

class RawImageUploadForm(ModelForm):
    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            name, ext = os.path.splitext(file.name)
            if ext.lower() not in supported_raw_formats():
                raise ValidationError(_('File type is not supported'))

        return file

    class Meta:
        model = RawImage
        fields = ('file',)
