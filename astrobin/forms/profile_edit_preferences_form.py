from django import forms
from django.conf import settings
from django.forms import SelectMultiple
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from astrobin.models import UserProfile
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import (
    can_remove_ads,
    can_remove_retailer_integration,
)


class UserProfileEditPreferencesForm(forms.ModelForm):
    agreed_to_iotd_tp_rules_and_guidelines_checkbox = forms.BooleanField(
        label=UserProfile._meta.get_field('agreed_to_iotd_tp_rules_and_guidelines').verbose_name,
        help_text=UserProfile._meta.get_field('agreed_to_iotd_tp_rules_and_guidelines').help_text,
        required=False
    )

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
            'agreed_to_iotd_tp_rules_and_guidelines_checkbox',
            'receive_important_communications',
            'receive_newsletter',
            'receive_marketing_and_commercial_material',
            'allow_astronomy_ads',
            'allow_retailer_integration',
            'enable_new_search_experience',
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

        valid_usersubscription = PremiumService(profile.user).get_valid_usersubscription()

        if not can_remove_ads(valid_usersubscription):
            self.fields['allow_astronomy_ads'].widget.attrs['disabled'] = True

        if not can_remove_retailer_integration(valid_usersubscription):
            self.fields['allow_retailer_integration'].widget.attrs['disabled'] = True

        if (self.instance and
                self.instance.agreed_to_iotd_tp_rules_and_guidelines and
                self.instance.agreed_to_iotd_tp_rules_and_guidelines > settings.IOTD_LAST_RULES_UPDATE):
            self.fields['agreed_to_iotd_tp_rules_and_guidelines_checkbox'].initial = True

    def save(self, commit=True):
        instance: UserProfile = super(UserProfileEditPreferencesForm, self).save(commit=False)

        if self.cleaned_data['agreed_to_iotd_tp_rules_and_guidelines_checkbox']:
            instance.agreed_to_iotd_tp_rules_and_guidelines = timezone.now()
        else:
            instance.agreed_to_iotd_tp_rules_and_guidelines = None

        if commit:
            instance.save(keep_deleted=True)

        return instance

    def clean_other_languages(self):
        data = self.cleaned_data['other_languages']
        if data:
            cleaned_data = ",".join(eval(data))
            return cleaned_data

        return data

    def clean_auto_submit_to_iotd_tp_process(self):
        auto_submit = self.cleaned_data['auto_submit_to_iotd_tp_process']
        user = self.instance.user

        if auto_submit and not IotdService.may_auto_submit_to_iotd_tp_process(user):
            raise forms.ValidationError(
                _(
                    'Sorry, you cannot automatically submit images for IOTD/TP consideration if you have not '
                    'had any images selected as Top Pick or Image of the Day before. Please submit images individually '
                    'using the Actions menu.'
                )
            )

        return auto_submit

    def clean(self):
        cleaned_data = super().clean()

        exclude_from_competitions = cleaned_data.get('exclude_from_competitions')
        auto_submit_to_iotd_tp_process = cleaned_data.get('auto_submit_to_iotd_tp_process')
        agreed_to_iotd_tp_rules_and_guidelines = cleaned_data.get('agreed_to_iotd_tp_rules_and_guidelines_checkbox')

        if exclude_from_competitions and auto_submit_to_iotd_tp_process:
            raise forms.ValidationError(
                _(
                    'You cannot be excluded from competitions and automatically submit images for IOTD/TP '
                    'consideration at the same time.'
                )
            )

        if auto_submit_to_iotd_tp_process and not agreed_to_iotd_tp_rules_and_guidelines:
            raise forms.ValidationError(
                _(
                    'You must agree to the IOTD/TP rules and guidelines before you can automatically submit images '
                    'for IOTD/TP consideration.'
                )
            )

        return cleaned_data
