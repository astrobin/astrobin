from django import forms

from astrobin.models import UserProfile


class UserProfileEditRetailerForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = UserProfile
        fields = (
            'retailer_country',
        )
