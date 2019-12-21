from django import forms

from astrobin.models import FocalReducer


class FocalReducerEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = FocalReducer
        exclude = ('make', 'name', 'retailed')
