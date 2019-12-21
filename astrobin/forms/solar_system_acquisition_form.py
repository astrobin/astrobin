from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.models import SolarSystem_Acquisition


class SolarSystem_AcquisitionForm(forms.ModelForm):
    error_css_class = 'error'

    date = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"),
        label=_("Date"),
    )

    def clean_seeing(self):
        data = self.cleaned_data['seeing']
        if data and data not in range(1, 6):
            raise forms.ValidationError(_("Please enter a value between 1 and 5."))

        return data

    def clean_transparency(self):
        data = self.cleaned_data['transparency']
        if data and data not in range(1, 11):
            raise forms.ValidationError(_("Please enter a value between 1 and 10."))

        return data

    class Meta:
        model = SolarSystem_Acquisition
        fields = (
            'date',
            'time',
            'frames',
            'fps',
            'focal_length',
            'cmi',
            'cmii',
            'cmiii',
            'seeing',
            'transparency',
        )
        widgets = {
            'date': forms.TextInput(attrs={'class': 'datepickerclass'}),
            'time': forms.TextInput(attrs={'class': 'timepickerclass'}),
        }
