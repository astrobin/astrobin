from django import forms

from astrobin.models import Image


class ImagePromoteForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('skip_notifications',)

    def __init__(self, **kwargs):
        super(ImagePromoteForm, self).__init__(**kwargs)
        if self.instance and self.instance.published:
            self.fields['skip_notifications'].widget = forms.HiddenInput()
