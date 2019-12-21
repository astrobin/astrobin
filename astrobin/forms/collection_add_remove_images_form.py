from django import forms

from astrobin.models import Collection


class CollectionAddRemoveImagesForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Collection
        fields = ('images',)
