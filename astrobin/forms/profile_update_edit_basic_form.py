from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from astrobin.models import Image, UserProfile


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
        fields = (
            'real_name',
            'skill_level',
            'website',
            'job',
            'hobbies',
            'instagram_username',
            'about',
        )

    def __init__(self, **kwargs):
        super(UserProfileEditBasicForm, self).__init__(**kwargs)

        self.fields['skill_level'].required = True
        self.fields['website'].label = _("Website")

    def clean_skill_level(self) -> str:
        skill_level = self.cleaned_data.get('skill_level')
        user = self.instance.user

        image_count = Image.objects_including_wip.filter(user=user).count()

        if image_count > 0 and skill_level == UserProfile.SKILL_LEVEL_NA:
            raise ValidationError(
                _(
                    'You have images on AstroBin, therefore you are an astrophotographer! :-) Please select a '
                    'different skill level.'
                )
            )

        return skill_level
