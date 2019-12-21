from django import forms
from django.utils.translation import ugettext_lazy as _


class BringToAttentionForm(forms.Form):
    users = forms.CharField(max_length=64, required=False)

    def __init__(self, user=None, **kwargs):
        super(BringToAttentionForm, self).__init__(**kwargs)
        self.fields['users'].label = _("Users")
