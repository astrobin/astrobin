from django import forms

from astrobin.models import Software


class SoftwareEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Software
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }
