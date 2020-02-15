from django import forms

from .models import PlateSolvingSettings, PlateSolvingAdvancedSettings


class PlateSolvingSettingsForm(forms.ModelForm):
    class Meta:
        model = PlateSolvingSettings
        exclude = []

    def __init__(self, *args, **kwargs):
        super(PlateSolvingSettingsForm, self).__init__(*args, **kwargs)
        instance = kwargs['instance']
        if instance and instance.blind:
            for field in self.fields:
                if field != 'blind':
                    self.fields[field].widget.attrs['disabled'] = 'disabled'


class PlateSolvingAdvancedSettingsForm(forms.ModelForm):
    class Meta:
        model = PlateSolvingAdvancedSettings
        exclude = []
