from django import forms

from astrobin.models import Filter


class FilterEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Filter
        exclude = ('make', 'name', 'retailed')
