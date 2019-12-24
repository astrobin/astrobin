from django import forms

from astrobin.models import UserProfile


class UserProfileEditCommercialForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = UserProfile
        fields = ('company_name', 'company_description', 'company_website',)
