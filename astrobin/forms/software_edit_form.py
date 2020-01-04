from django import forms

from astrobin.models import Software


class SoftwareEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Software
        exclude = ('make', 'name', 'retailed')
