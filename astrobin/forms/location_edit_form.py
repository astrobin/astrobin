from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.fields import COUNTRIES
from astrobin.models import Location


class LocationEditForm(forms.ModelForm):
    error_css_class = 'error'

    lat_deg = forms.IntegerField(
        label=_("Latitude (degrees)"),
        help_text="(0-90)",
        max_value=90,
        min_value=0)
    lat_min = forms.IntegerField(
        label=_("Latitude (minutes)"),
        help_text="(0-60)",
        max_value=60,
        min_value=0,
        required=False)
    lat_sec = forms.IntegerField(
        label=_("Latitude (seconds)"),
        help_text="(0-60)",
        max_value=60,
        min_value=0,
        required=False)

    lon_deg = forms.IntegerField(
        label=_("Longitude (degrees)"),
        help_text="(0-180)",
        max_value=180,
        min_value=0)
    lon_min = forms.IntegerField(
        label=_("Longitude (minutes)"),
        help_text="(0-60)",
        max_value=60,
        min_value=0,
        required=False)
    lon_sec = forms.IntegerField(
        label=_("Longitude (seconds)"),
        help_text="(0-60)",
        max_value=60,
        min_value=0,
        required=False)

    def __init__(self, **kwargs):
        super(LocationEditForm, self).__init__(**kwargs)
        self.fields['country'].choices = sorted(COUNTRIES, key=lambda c: c[1])

    class Meta:
        model = Location
        exclude = []
