from django import forms

from astrobin.models import UserProfile
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import can_remove_ads


class UserProfileEditPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'language',
            'default_frontpage_section',
            'default_gallery_sorting',
            'exclude_from_competitions',
            'receive_forum_emails',
            'receive_important_communications',
            'receive_newsletter',
            'receive_marketing_and_commercial_material',
            'allow_astronomy_ads',
        ]

    def __init__(self, **kwargs):
        super(UserProfileEditPreferencesForm, self).__init__(**kwargs)
        profile = getattr(self, 'instance', None)
        if not can_remove_ads(profile.user):
            self.fields['allow_astronomy_ads'].widget.attrs['disabled'] = True
