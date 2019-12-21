from django import forms

from astrobin.models import RetailedGear


class RetailedGearForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = RetailedGear
        fields = ('link', 'price', 'currency')
