from django import forms

from astrobin.models import FocalReducer


class FocalReducerEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = FocalReducer
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }
