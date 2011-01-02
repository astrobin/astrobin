from django import forms
from django.db import models

from models import Image
from models import UserProfile


class ImageUploadForm(forms.Form):
    file = forms.ImageField()


class ImageEditBasicForm(forms.Form):
    title = forms.CharField(max_length=64)
    subjects = forms.CharField(required=False)
    locations = forms.CharField(required=False)
    description = forms.CharField(widget=forms.Textarea, required=False)


class ImageEditGearForm(forms.Form):
    imaging_telescopes = forms.CharField(max_length=256)
    guiding_telescopes = forms.CharField(max_length=256)
    mounts = forms.CharField(max_length=256)
    imaging_cameras = forms.CharField(max_length=256)
    guiding_cameras = forms.CharField(max_length=256)
    focal_reducers = forms.CharField(max_length=256)
    software = forms.CharField(max_length=256)
    filters = forms.CharField(max_length=256)
    accessories = forms.CharField(max_length=256)


class UserProfileEditBasicForm(forms.ModelForm):
    locations = forms.CharField(max_length=64, required=False)
    class Meta:
        model = UserProfile
        fields = ('website', 'job', 'hobbies')


class UserProfileEditGearForm(forms.Form):
    telescopes = forms.CharField(max_length=256)
    mounts = forms.CharField(max_length=256)
    cameras = forms.CharField(max_length=256)
    focal_reducers = forms.CharField(max_length=256)
    software = forms.CharField(max_length=256)
    filters = forms.CharField(max_length=256)
    accessories = forms.CharField(max_length=256)
