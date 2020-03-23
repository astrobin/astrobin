from django import forms

from astrobin_apps_premium.models import DataLossCompensationRequest


class MigrateDonationsForm(forms.Form):
    pass


class DataLossCompensationRequestForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = DataLossCompensationRequest
        fields = '__all__'
