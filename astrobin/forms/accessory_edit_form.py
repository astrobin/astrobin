from django import forms

from astrobin.models import Accessory


class AccessoryEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Accessory
        exclude = ('make', 'name', 'retailed')
