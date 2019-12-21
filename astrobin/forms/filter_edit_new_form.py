from django import forms

from astrobin.models import Filter


class FilterEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Filter
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }
