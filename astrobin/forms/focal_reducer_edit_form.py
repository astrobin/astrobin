from django import forms

from astrobin.models import FocalReducer


class FocalReducerEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = FocalReducer
        exclude = ('make', 'name', 'migration_flag', 'migration_content_type', 'migration_object_id')
