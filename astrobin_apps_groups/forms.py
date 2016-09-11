# Django
from django import forms
from django.db.models import Q
from django.utils.translation import ugettext as _

# This app
from astrobin_apps_groups.models import *

class GroupUpdateBaseForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(GroupUpdateBaseForm, self).clean()
        category = cleaned_data.get("category")
        autosubmission = cleaned_data.get("autosubmission")

        if autosubmission and category not in (1, 11, 21, 31, 41):
            msg = "Only the following category support autosubmission: " \
                  "Professional network, Club or association, " \
                  "Internet commmunity, Friends or partners, Geographical area"

            self._errors['category'] = self.error_class([msg])
            del cleaned_data['category']

        return cleaned_data

    class Meta:
        model = Group
        fields = ['name', 'description', 'category', 'public', 'moderated', 'autosubmission',]


class GroupCreateForm(GroupUpdateBaseForm):
    pass


class GroupUpdateForm(GroupUpdateBaseForm):
    pass


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

