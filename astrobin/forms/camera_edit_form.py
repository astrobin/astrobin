from django import forms

from astrobin.models import Camera


class CameraEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Camera
        exclude = ('make', 'name', 'migration_flag', 'migration_content_type', 'migration_object_id')
