from django import forms
from django.db import models
from ajax_select.fields import AutoCompleteSelectMultipleField, AutoCompleteSelectField

from models import Image
from models import UserProfile

class ImageUploadForm(forms.Form):
    file = forms.ImageField()

class ImageUploadDetailsForm(forms.ModelForm):
    class Meta:
        model = Image

class UserProfileEditBasicForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('location', 'website', 'job', 'hobbies')

class UserProfileEditGearForm(forms.ModelForm):
    # declare a field and specify the named channel that it uses
    telescopes = AutoCompleteSelectMultipleField('telescope', required=False)
    class Meta:
        model = UserProfile
        fields = ('telescopes')
