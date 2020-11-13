from django import forms

from astrobin_apps_json_api.models import CkEditorFile


class CkEditorUploadForm(forms.ModelForm):
    class Meta:
        model = CkEditorFile
        fields = ('upload',)
