from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Div, Fieldset, HTML, Layout, Submit
from django import forms
from django.urls import reverse
from django.utils.translation import gettext

from astrobin.models import Image
from common.templatetags.common_tags import button_loading_class, button_loading_indicator
from .models import PlateSolvingSettings, PlateSolvingAdvancedSettings


class PlateSolvingSettingsForm(forms.ModelForm):
    class Meta:
        model = PlateSolvingSettings
        exclude = []

    def __init__(self, *args, **kwargs):
        image: Image = kwargs.pop('image')
        revision_label: str = kwargs.pop('revision_label')
        return_url: str = kwargs.pop('return_url')
        instance: PlateSolvingSettings = kwargs.get('instance')

        super(PlateSolvingSettingsForm, self).__init__(*args, **kwargs)


        self.helper = FormHelper()
        self.helper.form_id = 'platesolving-settings'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('image_edit_platesolving_settings', args=(image.get_id(), revision_label,))
        self.helper.attrs = {"novalidate": ''}
        self.helper.layout = Layout(
            Fieldset(
                '',
                'downsample_factor',
                'use_sextractor'
            ),
            Fieldset(
                '',
                'blind',
                'scale_units',
                'scale_min',
                'scale_max',
                'center_ra',
                'center_dec',
                'radius',
            ),
            Div(
                HTML(
                    f'<button '
                    f'  type="submit" '
                    f'  name="submit" '
                    f'  class="btn btn-primary btn-block-mobile {button_loading_class()}"'
                    f'>'
                    f'  {gettext("Save and plate-solve again")} {button_loading_indicator()}'
                    f'</button>'
                ),
                HTML(
                    f'<a '
                    f'  class="btn btn-block-mobile"'
                    f'  href="{return_url}"'
                    f'>'
                    f'  {gettext("Cancel")}'
                    f'</a>'
                ),
                css_class='form-actions',
            )
        )

        if instance and instance.blind:
            non_blind_fields = [
                'scale_units',
                'scale_min',
                'scale_max',
                'center_ra',
                'center_dec',
                'radius',
            ]
            for field in non_blind_fields:
                self.fields[field].widget.attrs['disabled'] = 'disabled'


class PlateSolvingAdvancedSettingsForm(forms.ModelForm):
    class Meta:
        model = PlateSolvingAdvancedSettings
        exclude = []
