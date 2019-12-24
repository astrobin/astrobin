from django import forms

from astrobin.models import Camera


class CameraEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Camera
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }
