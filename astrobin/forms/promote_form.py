from django import forms

from astrobin.models import Image


class ImagePromoteForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = (
            'skip_notifications',
            'skip_activity_stream',
        )
        widgets = {
            'skip_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'skip_activity_stream': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, **kwargs):
        super(ImagePromoteForm, self).__init__(**kwargs)
        if self.instance and self.instance.published:
            self.fields['skip_notifications'].widget = forms.HiddenInput()
            self.fields['skip_activity_stream'].widget = forms.HiddenInput()
