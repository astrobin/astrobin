from django import forms

from astrobin.models import Camera


class CameraEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Camera
        exclude = ('make', 'name', 'retailed')
