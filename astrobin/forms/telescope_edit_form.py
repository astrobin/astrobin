from django import forms

from astrobin.models import Telescope


class TelescopeEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Telescope
        exclude = ('make', 'name', 'retailed')
