from django import forms

from astrobin.models import UserProfile


class UserProfileEditPrivacyForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'display_member_since',
            'display_last_seen',
        ]
