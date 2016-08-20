# Django
from django import forms

# This app
from astrobin_apps_groups.models import *


class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'category', 'public', 'moderated']


class GroupUpdateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'category', 'public', 'moderated']


class GroupInviteForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['invited_users']
