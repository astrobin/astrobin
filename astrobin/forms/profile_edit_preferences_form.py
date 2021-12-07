from django import forms
from django.conf import settings
from django.forms import SelectMultiple
from django.utils.translation import ugettext_lazy as _

from astrobin.models import UserProfile
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import (
    can_remove_ads,
    can_remove_retailer_integration,
)


class UserProfileEditPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'language',
            'other_languages',
            'default_frontpage_section',
            'default_gallery_sorting',
            'display_wip_images_on_public_gallery',
            'open_notifications_in_new_tab',
            'exclude_from_competitions',
            'auto_submit_to_iotd_tp_process',
            'receive_important_communications',
            'receive_newsletter',
            'receive_marketing_and_commercial_material',
            'allow_astronomy_ads',
            'allow_retailer_integration',
        ]
        widgets = {
            'other_languages': SelectMultiple(
                choices=settings.ALL_LANGUAGE_CHOICES,
                attrs={
                    'class': 'select2'
                })
        }

    def __init__(self, **kwargs):
        super(UserProfileEditPreferencesForm, self).__init__(**kwargs)
        profile = getattr(self, 'instance', None)

        if not can_remove_ads(profile.user):
            self.fields['allow_astronomy_ads'].widget.attrs['disabled'] = True

        if not can_remove_retailer_integration(profile.user):
            self.fields['allow_retailer_integration'].widget.attrs['disabled'] = True

    def clean_other_languages(self):
        data = self.cleaned_data['other_languages']
        if data:
            cleaned_data = ",".join(eval(data))
            return cleaned_data

        return data

    def clean(self):
        cleaned_data = super().clean()

        exclude_from_competitions = cleaned_data.get('exclude_from_competitions')
        auto_submit_to_iotd_tp_process = cleaned_data.get('auto_submit_to_iotd_tp_process')

        if exclude_from_competitions and auto_submit_to_iotd_tp_process:
            raise forms.ValidationError(
                _(
                    'You cannot be excluded from competitions and automatically submit images for IOTD/TP '
                    'consideration at the same time.'
                )
            )

        return cleaned_data
