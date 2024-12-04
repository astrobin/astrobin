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
    nullable_boolean_field_choices = (
        ('None', _('Let AstroBin decide')),
        ('True', _('Yes')),
        ('False', _('No')),
    )

    agreed_to_iotd_tp_rules_and_guidelines_checkbox = forms.BooleanField(
        label=UserProfile._meta.get_field('agreed_to_iotd_tp_rules_and_guidelines').verbose_name,
        help_text=UserProfile._meta.get_field('agreed_to_iotd_tp_rules_and_guidelines').help_text,
        required=False
    )

    enable_new_search_experience = forms.ChoiceField(
        required=False,
        choices=nullable_boolean_field_choices,
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
        profile: UserProfile = getattr(self, 'instance', None)

        valid_usersubscription = PremiumService(profile.user).get_valid_usersubscription()

        if not can_remove_ads(valid_usersubscription):
            self.fields['allow_astronomy_ads'].widget.attrs['disabled'] = True

        if profile.enable_new_search_experience is None:
            self.fields['enable_new_search_experience'].initial = 'None'
        else:
            self.fields['enable_new_search_experience'].initial = str(profile.enable_new_search_experience)

        if profile.may_enable_new_gallery_experience:
            self.fields['enable_new_gallery_experience'] = forms.ChoiceField(
                required=False,
                choices=self.nullable_boolean_field_choices,
            )
            if profile.enable_new_gallery_experience is None:
                self.fields['enable_new_gallery_experience'].initial = 'None'
            else:
                self.fields['enable_new_gallery_experience'].initial = str(profile.enable_new_gallery_experience)

        if not can_remove_retailer_integration(valid_usersubscription):
            self.fields['allow_retailer_integration'].widget.attrs['disabled'] = True

        if (
                self.instance and
                self.instance.agreed_to_iotd_tp_rules_and_guidelines and
                self.instance.agreed_to_iotd_tp_rules_and_guidelines > settings.IOTD_LAST_RULES_UPDATE
        ):
            self.fields['agreed_to_iotd_tp_rules_and_guidelines_checkbox'].initial = True

    def save(self, commit=True):
        instance: UserProfile = super(UserProfileEditPreferencesForm, self).save(commit=False)

        if self.cleaned_data['agreed_to_iotd_tp_rules_and_guidelines_checkbox']:
            instance.agreed_to_iotd_tp_rules_and_guidelines = timezone.now()
        else:
            instance.agreed_to_iotd_tp_rules_and_guidelines = None

        if 'enable_new_search_experience' in self.cleaned_data:
            instance.enable_new_search_experience = self.cleaned_data['enable_new_search_experience']

        if 'enable_new_gallery_experience' in self.cleaned_data:
            instance.enable_new_gallery_experience = self.cleaned_data['enable_new_gallery_experience']

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

    def clean_enable_new_search_experience(self):
        value = self.cleaned_data['enable_new_search_experience']
        if value == 'None':
            return None
        return value == 'True'

    def clean_enable_new_gallery_experience(self):
        value = self.cleaned_data['enable_new_gallery_experience']
        if value == 'None':
            return None
        return value == 'True'

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
