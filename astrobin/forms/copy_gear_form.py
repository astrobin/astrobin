from django import forms

from astrobin.models import Image


class CopyGearForm(forms.Form):
    image = forms.ModelChoiceField(
        queryset=None,
    )

    def __init__(self, user, **kwargs):
        super(CopyGearForm, self).__init__(**kwargs)
        self.fields['image'].queryset = Image.objects_including_wip.filter(user=user)
