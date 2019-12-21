from django import forms

from astrobin.models import Mount


class MountEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Mount
        exclude = ('make', 'name', 'retailed')
