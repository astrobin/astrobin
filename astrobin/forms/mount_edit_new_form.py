from django import forms

from astrobin.models import Mount


class MountEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Mount
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }
