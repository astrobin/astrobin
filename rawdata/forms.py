# Python
import os

# Django
from django import forms
from django.utils.translation import ugettext_lazy as _

# This app
from .models import (
    RawImage,
    PublicDataPool,
    PrivateSharedFolder,
)
from .utils import supported_raw_formats

class RawImageUploadForm(forms.ModelForm):
    error_css_class = 'error'

    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            name, ext = os.path.splitext(file.name)
            if ext.lower().strip('.') not in supported_raw_formats():
                raise forms.ValidationError(_('File type is not supported'))

        return file

    class Meta:
        model = RawImage
        fields = ('file',)


class PublicDataPoolForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = PublicDataPool
        fields = ('name', 'description',)


class PublicDataPool_SelectExistingForm(forms.Form):
    error_css_class = 'error'

    existing_pools = forms.ChoiceField(
        label = '',
        choices = [],
    )

    def __init__(self, **kwargs):
        super(PublicDataPool_SelectExistingForm, self).__init__(**kwargs)
        # Init choices here to prevent stagnation due to django caching.
        self.fields['existing_pools'].choices = PublicDataPool.objects.all().values_list('id', 'name')


class PublicDataPool_ImagesForm(forms.ModelForm):
    error_css_class= 'error'

    class Meta:
        model = PublicDataPool
        fields = ('images',)


class PrivateSharedFolderForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = PrivateSharedFolder
        fields = ('name', 'description',)


class PrivateSharedFolder_SelectExistingForm(forms.Form):
    error_css_class = 'error'

    existing_folders = forms.ChoiceField(
        label = '',
        choices = [],
    )

    def __init__(self, **kwargs):
        super(PrivateSharedFolder_SelectExistingForm, self).__init__(**kwargs)
        # Init choices here to prevent stagnation due to django caching.
        self.fields['existing_folders'].choices = PrivateSharedFolder.objects.all().values_list('id', 'name')


class PrivateSharedFolder_ImagesForm(forms.ModelForm):
    error_css_class= 'error'

    class Meta:
        model = PrivateSharedFolder
        fields = ('images',)

