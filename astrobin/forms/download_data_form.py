from django import forms

from astrobin.models import DataDownloadRequest


class DownloadDataForm(forms.ModelForm):
    class Meta:
        model = DataDownloadRequest
        fields = []
