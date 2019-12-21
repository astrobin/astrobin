from django import forms

from astrobin.models import Accessory


class AccessoryEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Accessory
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }
