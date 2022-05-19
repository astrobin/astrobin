from datetime import datetime as dt

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from astrobin.models import DeepSky_Acquisition, Filter, Image
from astrobin_apps_equipment.templatetags.astrobin_apps_equipment_tags import is_own_equipment_migrator
from astrobin_apps_equipment.models import Filter as FilterV2

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

    def __init__(self, user: User = None, image: Image = None, **kwargs):
        super().__init__(**kwargs)

        if is_own_equipment_migrator(user):
            filter_2_queryset = image.filters_2.all() if image else FilterV2.objects.none()
            self.fields['filter_2'].queryset = filter_2_queryset
            self.fields.pop('filter')
        else:
            filters_from_profile = list(user.userprofile.filters.values_list('pk', flat=True))
            filters_from_images = list(
                Filter.objects.filter(images_using__user=user).distinct().values_list('pk', flat=True)
            )
            filter_queryset = Filter.objects.filter(pk__in=set(filters_from_images + filters_from_profile))
            self.fields['filter'].queryset = filter_queryset
            self.fields.pop('filter_2')

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
