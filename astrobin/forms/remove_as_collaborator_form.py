from django import forms

from astrobin.models import Image


class ImageRemoveAsCollaboratorForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ()
