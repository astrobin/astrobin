from datetime import datetime as dt

from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.models import DeepSky_Acquisition, Filter


class DeepSky_AcquisitionForm(forms.ModelForm):
    error_css_class = 'error'

    date = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'datepickerclass', 'autocomplete': 'off'}),
        help_text=_("Please use the following format: yyyy-mm-dd"),
        label=_("Date"),
    )

    class Meta:
        model = DeepSky_Acquisition
        exclude = []

    def __init__(self, user=None, **kwargs):
        super().__init__(**kwargs)

        filters_from_profile = list(user.userprofile.filters.values_list('pk', flat=True))
        filters_from_images = list(
            Filter.objects.filter(images_using__user=user).distinct().values_list('pk', flat=True)
        )
        filter_queryset = Filter.objects.filter(pk__in=set(filters_from_images + filters_from_profile))

        self.fields['filter'].queryset = filter_queryset
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
