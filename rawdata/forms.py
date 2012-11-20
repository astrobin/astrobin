# Python
import os

# Django
from django.forms import ModelForm, ValidationError
from django.utils.translation import ugettext_lazy as _

# This app
from .models import RawImage

class RawImageUploadForm(ModelForm):
    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            name, ext = os.path.splitext(file.name)
            supported_types = ('fit', 'fits', 'cr2')
            if ext.lower() not in supported_types:
                raise ValidationError(_('File type is not supported'))

        return file

    class Meta:
        model = RawImage
        fields = ('file',)
