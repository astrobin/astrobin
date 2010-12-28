from django import forms
from django.db import models

from models import Image
from models import UserProfile

class ImageUploadForm(forms.Form):
    file = forms.ImageField()

class ImageEditBasicForm(forms.Form):
    title = forms.CharField(max_length=128)
    subjects = forms.CharField(required=False)
    description = forms.CharField(widget=forms.Textarea, required=False)

class ImageEditGearForm(forms.Form):
    imaging_telescopes = forms.CharField()
    guiding_telescopes = forms.CharField()
    mounts = forms.CharField()
    cameras = forms.CharField()
    focal_reducers = forms.CharField()
    software = forms.CharField()
    filters = forms.CharField()

class ImageEditAcquisitionForm(forms.Form):
    pass

class UserProfileEditBasicForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('location', 'website', 'job', 'hobbies')

class UserProfileEditGearForm(forms.Form):
    telescopes = forms.CharField()
    mounts = forms.CharField()
    cameras = forms.CharField()
    focal_reducers = forms.CharField()
    software = forms.CharField()
    filters = forms.CharField()

