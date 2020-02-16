from django import forms
from django.utils.translation import ugettext as _

from astrobin_apps_groups.models import Group


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


class GroupCreateForm(GroupUpdateBaseForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'category', 'public', 'moderated', 'autosubmission', ]


class GroupUpdateForm(GroupUpdateBaseForm):
    autosubmission_deactivation_strategy = forms.ChoiceField(
        label=_("Autosubmission deactivation strategy"),
        choices=(
            ('keep', _("Keep all images currently auto-submitted")),
            ('delete', _("Remove all images and start over")),
        ),
        help_text=_(
            "When changing your group from autosubmission to non-autosubmission, you need to think of what to do with the images currently in the group."),
        required=False,
    )

    class Meta:
        model = Group
        fields = [
            'name', 'description', 'category', 'public', 'moderated',
            'autosubmission', 'autosubmission_deactivation_strategy', ]


class GroupInviteForm(forms.ModelForm):
    invite_users = forms.CharField(
        label=_("Invite users"),
        help_text=_("Users will receive a notification and will be able to join the group"),
    )

    class Meta:
        model = Group
        fields = ['invite_users']


class GroupSelectForm(forms.Form):
    groups = forms.ChoiceField(
        label='',
        choices=[],
    )

    def __init__(self, user, **kwargs):
        super(GroupSelectForm, self).__init__(**kwargs)
        self.fields['groups'].choices = Group.objects \
            .filter(autosubmission=False, members=user) \
            .distinct() \
            .values_list('id', 'name')
