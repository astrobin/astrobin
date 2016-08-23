# Django
from django import forms
from django.utils.translation import ugettext as _

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
    invite_users = forms.CharField(
        label = _("Invite users"),
        help_text = _("Users will receive a notification and will be able to join the group"),
    )

    class Meta:
        model = Group
        fields = ['invite_users']
