import datetime

from django import forms

from astrobin.models import Gear
from astrobin.utils import uniq


class ModeratorGearFixForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Gear
        fields = ('make', 'name',)

    def __init__(self, **kwargs):
        super(ModeratorGearFixForm, self).__init__(**kwargs)
        self.widgets['make'] = forms.TextInput(attrs={
            'data-provide': 'typeahead',
            'data-source': simplejson.dumps(
                uniq([x.make for x in Gear.objects.exclude(make=None).exclude(make='')])),
            'autocomplete': 'off',
        })

    def clean_make(self):
        return self.cleaned_data['make'].strip()

    def clean_name(self):
        return self.cleaned_data['name'].strip()

    def save(self, force_insert=False, force_update=False, commit=True):
        instance = getattr(self, 'instance', None)
        old_make = Gear.objects.get(id=instance.id).make
        old_name = Gear.objects.get(id=instance.id).name

        m = super(ModeratorGearFixForm, self).save(commit=False)

        # Update the time
        m.moderator_fixed = datetime.datetime.now()

        if commit:
            m.save()

        return m
