# Django
from django import forms

# This app
from .models import PlateSolvingSettings


class PlateSolvingSettingsForm(forms.ModelForm):
    class Meta:
        model = PlateSolvingSettings
