from django import forms

from astrobin.models import ImageRevision


class ImageRevisionUploadForm(forms.ModelForm):
    class Meta:
        model = ImageRevision
        fields = ('image_file', 'description', 'skip_notifications')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'skip_notifications': forms.CheckboxInput()
        }
