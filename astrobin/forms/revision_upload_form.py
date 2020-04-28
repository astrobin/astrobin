from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.models import ImageRevision


class ImageRevisionUploadForm(forms.ModelForm):
    error_css_class = 'error'

    mark_as_final = forms.BooleanField(
        required=False,
        label=_("Mark as final"),
        initial=True
    )

    class Meta:
        model = ImageRevision
        fields = ('image_file', 'description', 'skip_notifications', 'mark_as_final')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'skip_notifications': forms.CheckboxInput()
        }
