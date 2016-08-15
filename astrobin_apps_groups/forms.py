# Django
from django import forms

# This app
from astrobin_apps_groups.models import *


class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = Group


class GroupUpdateForm(forms.ModelForm):
    class Meta:
        model = Group
