from django import forms

from astrobin.models import Collection


class CollectionUpdateForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Collection
        fields = ('name', 'description', 'cover',)
