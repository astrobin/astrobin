from django import forms
from django.db import models

from models import Image

class ImageUploadForm(forms.Form):
    file = forms.ImageField()

class ImageUploadDetailsForm(forms.ModelForm):
    class Meta:
        model = Image
