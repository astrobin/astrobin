from datetime import datetime as dt

from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.models import DeepSky_Acquisition


class DeepSky_AcquisitionBasicForm(forms.ModelForm):
    error_css_class = 'error'

    date = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"),
        label=_("Date"),
    )

    def clean_date(self):
        date = self.cleaned_data['date']
        if date and date > dt.today().date():
            raise forms.ValidationError(_("The date cannot be in the future."))
        return date

    class Meta:
        model = DeepSky_Acquisition
        fields = ('date', 'number', 'duration',)
        widgets = {
            'date': forms.TextInput(attrs={'class': 'datepickerclass'}),
        }
