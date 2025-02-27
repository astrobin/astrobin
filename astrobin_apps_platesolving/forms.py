from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset, HTML, Layout
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
                'astrometry_net_publicly_visible',
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
        
    def __init__(self, *args, **kwargs):
        # The solution parameter is optional but recommended for radius-based field filtering
        self.solution = kwargs.pop('solution', None)
        self.radius_category = None
        self.hidden_fields = []
        
        super(PlateSolvingAdvancedSettingsForm, self).__init__(*args, **kwargs)
        
        # Apply field visibility rules based on solution radius
        if self.solution and hasattr(self.solution, 'radius') and self.solution.radius:
            from astrobin_apps_platesolving.services.solution_service import SolutionService
            import logging
            log = logging.getLogger(__name__)
            
            try:
                # Convert radius to float
                radius = float(self.solution.radius)
                
                # Get radius category
                radius_category = SolutionService.get_radius_category(radius)
                log.debug(f"Form init: solution radius = {radius}, category = {radius_category}")

                if radius_category:
                    # Translate the radius category
                    from django.utils.translation import gettext as _
                    radius_categories = {
                        "very_large": _("Very Large Field (>30 degrees)"),
                        "large": _("Large Field (15-30 degrees)"),
                        "medium": _("Medium Field (4-15 degrees)"),
                        "small": _("Small Field (1-4 degrees)"),
                        "very_small": _("Very Small Field (<1 degree)")
                    }
                    self.radius_category = radius_categories.get(radius_category, radius_category)
                    
                    # Hide fields based on the technical radius category
                    self._hide_inappropriate_fields(radius_category)
            except (ValueError, TypeError) as e:
                log.error(f"Error processing solution radius: {e}")
                
    def _hide_inappropriate_fields(self, radius_category):
        """
        Hide fields that should not be editable based on the radius category.
        These fields correspond to features that should be off by default for a given radius.
        """
        from astrobin_apps_platesolving.services.solution_service import SolutionService
        import logging
        log = logging.getLogger(__name__)
        
        # Get default settings for this category directly from the service
        default_settings_dict = SolutionService.get_default_advanced_settings_for_radius_category(radius_category)
        
        # Convert the dictionary to an object for easier attribute access
        from astrobin_apps_platesolving.models import PlateSolvingAdvancedSettings
        default_settings = PlateSolvingAdvancedSettings()
        for key, value in default_settings_dict.items():
            setattr(default_settings, key, value)
        
        # For each feature that should be OFF by default, hide the field
        self.hidden_fields = []
        for field_name in list(self.fields.keys()):  # Create a copy of keys to avoid modification during iteration
            if field_name.startswith('show_') and hasattr(default_settings, field_name):
                default_value = getattr(default_settings, field_name)
                if not default_value:  # If it should be OFF by default
                    # Remove the field from the form
                    self.fields.pop(field_name, None)
                    
                    # Also remove related magnitude limits if they exist
                    if field_name == 'show_hd' and 'hd_max_magnitude' in self.fields:
                        self.fields.pop('hd_max_magnitude', None)
                    elif field_name == 'show_gcvs' and 'gcvs_max_magnitude' in self.fields:
                        self.fields.pop('gcvs_max_magnitude', None)
                    elif field_name == 'show_tycho_2' and 'tycho_2_max_magnitude' in self.fields:
                        self.fields.pop('tycho_2_max_magnitude', None)
                    
                    # Get a human-readable field name
                    from django.utils.translation import gettext as _
                    field_label = _(field_name.replace('show_', '').replace('_', ' ').title())
                    self.hidden_fields.append(field_label)
                    
        log.debug(f"Hidden fields for radius category {radius_category}: {self.hidden_fields}")
