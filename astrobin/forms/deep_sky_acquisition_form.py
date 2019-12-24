from datetime import datetime as dt

from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.models import DeepSky_Acquisition


class DeepSky_AcquisitionForm(forms.ModelForm):
    error_css_class = 'error'

    date = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"),
        label=_("Date"),
    )

    class Meta:
        model = DeepSky_Acquisition
        exclude = []

    def __init__(self, user=None, **kwargs):
        queryset = None
        try:
            queryset = kwargs.pop('queryset')
        except KeyError:
            pass

        super(DeepSky_AcquisitionForm, self).__init__(**kwargs)
        if queryset:
            self.fields['filter'].queryset = queryset
        self.fields['number'].required = True
        self.fields['duration'].required = True

    def save(self, force_insert=False, force_update=False, commit=True):
        m = super(DeepSky_AcquisitionForm, self).save(commit=False)
        m.advanced = True
        if commit:
            m.save()
        return m

    def clean_date(self):
        date = self.cleaned_data['date']
        if date and date > dt.today().date():
            raise forms.ValidationError(_("The date cannot be in the future."))
        return date
