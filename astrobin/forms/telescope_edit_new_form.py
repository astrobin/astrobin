from django import forms

from astrobin.models import Telescope


class TelescopeEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Telescope
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }
