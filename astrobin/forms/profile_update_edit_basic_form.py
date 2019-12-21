from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.models import UserProfile


class UserProfileEditBasicForm(forms.ModelForm):
    error_css_class = 'error'

    website = forms.RegexField(
        regex='^(http|https)://',
        required=False,
        help_text=_("If you have a personal website, put the address here."),
        error_messages={'invalid': "The address must start with http:// or https://."},
    )

    class Meta:
        model = UserProfile
        fields = ('real_name', 'website', 'job', 'hobbies', 'timezone', 'about')

    def __init__(self, **kwargs):
        super(UserProfileEditBasicForm, self).__init__(**kwargs)
        self.fields['website'].label = _("Website")
