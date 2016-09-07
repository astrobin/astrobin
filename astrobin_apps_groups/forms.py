# Django
from django import forms
from django.db.models import Q
from django.utils.translation import ugettext as _

# This app
from astrobin_apps_groups.models import *


class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'category', 'public', 'moderated', 'autosubmission',]


class GroupUpdateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'category', 'public', 'moderated', 'autosubmission',]


class GroupInviteForm(forms.ModelForm):
    invite_users = forms.CharField(
        label = _("Invite users"),
        help_text = _("Users will receive a notification and will be able to join the group"),
    )

    class Meta:
        model = Group
        fields = ['invite_users']


class GroupSelectForm(forms.Form):
    groups = forms.ChoiceField(
        label = '',
        choices = [],
    )

    def __init__(self, user, **kwargs):
        super(GroupSelectForm, self).__init__(**kwargs)
        self.fields['groups'].choices = Group.objects\
            .filter(autosubmission = False)\
            .filter(
                Q(owner = user) |
                Q(members = user))\
            .distinct()\
            .values_list('id', 'name')

