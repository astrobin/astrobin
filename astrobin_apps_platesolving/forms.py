# Django
from django import forms

# This app
from .models import PlateSolvingSettings


class PlateSolvingSettingsForm(forms.ModelForm):
    class Meta:
        model = PlateSolvingSettings

    def __init__(self, *args, **kwargs):
        super(PlateSolvingSettingsForm, self).__init__(*args, **kwargs)
        instance = kwargs['instance']
        if instance and instance.blind:
            for field in self.fields:
                if field != 'blind':
                    self.fields[field].widget.attrs['disabled'] = 'disabled'
