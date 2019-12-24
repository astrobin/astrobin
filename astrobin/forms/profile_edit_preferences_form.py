from django import forms

from astrobin.models import UserProfile


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
            'receive_marketing_and_commercial_material'
        ]
