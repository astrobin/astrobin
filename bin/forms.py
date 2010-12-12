from django import forms
from django.db import models

from models import Image
from models import UserProfile

class ImageUploadForm(forms.Form):
    file = forms.ImageField()

class ImageUploadDetailsForm(forms.Form):
    title = forms.CharField(max_length=128)
    subjects = forms.CharField()
    description = forms.CharField(widget=forms.Textarea)

class UserProfileEditBasicForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('location', 'website', 'job', 'hobbies')

class UserProfileEditGearForm(forms.Form):
    telescopes = forms.CharField()
    mounts = forms.CharField()
    cameras = forms.CharField()
    focal_reducers = forms.CharField()

