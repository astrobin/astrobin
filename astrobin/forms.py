from django import forms
from django.db import models

from models import Image
from models import UserProfile


class ImageUploadForm(forms.Form):
    file = forms.ImageField()


class ImageEditBasicForm(forms.Form):
    title = forms.CharField(max_length=64)
    subjects = forms.CharField(required=False)
    locations = forms.CharField(required=False, help_text="<noscript>*</noscript>")
    description = forms.CharField(widget=forms.Textarea, required=False)


class ImageEditGearForm(forms.Form):
    imaging_telescopes = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    guiding_telescopes = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    mounts = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    imaging_cameras = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    guiding_cameras = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    focal_reducers = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    software = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    filters = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    accessories = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")


class UserProfileEditBasicForm(forms.ModelForm):
    locations = forms.CharField(max_length=64, required=False, help_text="<noscript>*</noscript>")
    class Meta:
        model = UserProfile
        fields = ('website', 'job', 'hobbies')


class UserProfileEditGearForm(forms.Form):
    telescopes = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    mounts = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    cameras = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    focal_reducers = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    software = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    filters = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    accessories = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")


class PrivateMessageForm(forms.Form):
    subject = forms.CharField(max_length=255, required=False)
    body = forms.CharField(widget=forms.Textarea, max_length=4096, required=False)


class BringToAttentionForm(forms.Form):
    user = forms.CharField(max_length=64, required=False)


class ImageRevisionUploadForm(forms.Form):
    file = forms.ImageField()

