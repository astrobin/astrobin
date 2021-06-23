from django import forms

from astrobin.models import Mount


class MountEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Mount
        exclude = ('make', 'name', 'migration_flag', 'migration_content_type', 'migration_object_id')
