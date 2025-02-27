import logging
import random
import string
import urllib.request, urllib.parse, urllib.error
from typing import Optional, Dict, Any

from django.conf import settings
from django.urls import reverse

from astrobin.templatetags.tags import thumbnail_scale
from astrobin_apps_platesolving.backends.base import AbstractPlateSolvingBackend
from astrobin_apps_platesolving.models import PlateSolvingAdvancedSettings, PlateSolvingAdvancedTask
from astrobin_apps_platesolving.services.solution_service import SolutionService

log = logging.getLogger(__name__)


class Solver(AbstractPlateSolvingBackend):
    def start(self, image_url, **kwargs):
        advanced_settings: Optional[PlateSolvingAdvancedSettings] = kwargs.pop('advanced_settings', None)
        image_width: int = kwargs.pop('image_width')
        image_height: int = kwargs.pop('image_height')
        small_size_ratio: float = thumbnail_scale(image_width, 'hd', 'regular')
        pixscale: float = kwargs.pop('pixscale')
        hd_width: int = min(image_width, settings.THUMBNAIL_ALIASES['']['hd']['size'][0])
        hd_ratio: float = max(1.0, image_width / float(hd_width))
        hd_height: int = int(image_height / hd_ratio)
        settings_hd_width: int = settings.THUMBNAIL_ALIASES['']['hd']['size'][0]
        
        # Get radius from kwargs
        radius = kwargs.pop('radius', None)
        
        if image_width > settings_hd_width and advanced_settings and not advanced_settings.sample_raw_frame_file:
            ratio = image_width / float(settings_hd_width)
            pixscale = float(pixscale) * ratio

        # Check if we need to enforce limitations based on the radius category
        if advanced_settings and radius is not None:
            radius_category = SolutionService.get_radius_category(radius)
            log.debug(f"Radius: {radius} - Radius category: {radius_category}")
            if radius_category:
                self._enforce_setting_limitations(advanced_settings, radius_category)

        task_params = [
            'imageURL=%s' % image_url,
            'centerRA=%f' % kwargs.pop('ra'),
            'centerDec=%f' % kwargs.pop('dec'),
            'largeSize=%d' % max(hd_width, hd_height),
            'smallSizeRatio=%f' % small_size_ratio,
            'imageResolution=%f' % pixscale,
            'fontsBaseURL=%s' % settings.STATIC_URL + 'astrobin/fonts',
            'liveLogURL=%s' % settings.BASE_URL + reverse('astrobin_apps_platesolving.pixinsight_live_log_webhook')
        ]

        observation_time = kwargs.pop('observation_time')
        if observation_time is not None:
            task_params.append('observationTime=%sT00:00:00Z' % observation_time)

        latitude = kwargs.pop('latitude')
        if latitude is not None:
            task_params.append('obsLatitude=%f' % latitude)

        longitude = kwargs.pop('longitude')
        if longitude is not None:
            task_params.append('obsLongitude=%f' % longitude)

        altitude = kwargs.pop('altitude')
        if altitude is not None:
            task_params.append('obsHeight=%f' % altitude)

        layers = []
        if advanced_settings:
            if advanced_settings.show_grid:
                layers.append('Grid')
            if advanced_settings.show_ecliptic:
                layers.append('Ecliptic')
            if advanced_settings.show_galactic_equator:
                layers.append('Galactic Equator')
            if advanced_settings.show_constellation_borders:
                layers.append('Constellation Borders')
            if advanced_settings.show_constellation_lines:
                layers.append('Constellation Lines')
            if advanced_settings.show_named_stars:
                layers.append('NamedStars')
            if advanced_settings.show_hd:
                layers.append('HD Cross-Reference')
            if advanced_settings.show_messier:
                layers.append('Messier')
            if advanced_settings.show_ngc_ic:
                layers.append('NGC-IC')
            if advanced_settings.show_vdb:
                layers.append('VdB')
            if advanced_settings.show_sharpless:
                layers.append('Sharpless')
            if advanced_settings.show_barnard:
                layers.append('Barnard')
            if advanced_settings.show_lbn:
                layers.append('LBN')
            if advanced_settings.show_ldn:
                layers.append('LDN')
            if advanced_settings.show_pgc:
                layers.append('PGC')
            if advanced_settings.show_planets:
                layers.append('Planets')
            if advanced_settings.show_asteroids:
                layers.append('Asteroids')
            if advanced_settings.show_gcvs:
                layers.append('GCVS')
            if advanced_settings.show_tycho_2:
                layers.append('TYCHO-2')
            if advanced_settings.show_cgpn:
                layers.append('CGPN')
            if advanced_settings.show_quasars:
                layers.append('Milliquas')

            if advanced_settings.scaled_font_size == 'S':
                task_params.append('smallSizeTextRatio=%f' % .66)
                task_params.append('textScale=%f' % .66)
            elif advanced_settings.scaled_font_size == 'M':
                task_params.append('smallSizeTextRatio=%f' % .9)
                task_params.append('textScale=%f' % .9)
            elif advanced_settings.scaled_font_size == 'L':
                task_params.append('smallSizeTextRatio=%f' % 1.33)
                task_params.append('textScale=%f' % 1.33)

        if len(layers) > 0:
            task_params.append('layers=%s' % '|'.join(layers))

        layer_max_magnitudes = []
        for layer in layers:
            if layer == 'HD Cross-Reference' and advanced_settings.hd_max_magnitude is not None:
                layer_max_magnitudes.append(str(advanced_settings.hd_max_magnitude))
            elif layer == 'GCVS' and advanced_settings.gcvs_max_magnitude is not None:
                layer_max_magnitudes.append(str(advanced_settings.gcvs_max_magnitude))
            elif layer == 'TYCHO-2' and advanced_settings.tycho_2_max_magnitude is not None:
                layer_max_magnitudes.append(str(advanced_settings.tycho_2_max_magnitude))
            else:
                layer_max_magnitudes.append("")

        if len(layer_max_magnitudes) > 0:
            task_params.append(f'layerMagnitudeLimits={"|".join(layer_max_magnitudes)}')

        # Get priority from kwargs, default to 'normal'
        priority = kwargs.pop('priority', 'normal')
        if priority not in ('normal', 'low'):
            priority = 'normal'

        task = PlateSolvingAdvancedTask.objects.create(
            serial_number=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32)),
            task_params=urllib.parse.quote('\n'.join(task_params)),
            priority=priority,
        )

        log.debug("PixInsight plate-solving: created task %s" % task.serial_number)
        return task.serial_number
        
    def _enforce_setting_limitations(self, advanced_settings: PlateSolvingAdvancedSettings, radius_category: str) -> None:
        """
        Enforce setting limitations based on the radius category.
        This prevents enabling features that should be off by default for the given radius category,
        but allows users to turn off any feature they want.
        """
        log.debug(f"Enforcing settings limitations for radius category: {radius_category}")
        
        # Get default settings for this category directly from the service
        default_settings_dict = SolutionService.get_default_advanced_settings_for_radius_category(radius_category)
        
        # Convert the dictionary to an object for easier attribute access
        default_settings = PlateSolvingAdvancedSettings()
        for key, value in default_settings_dict.items():
            setattr(default_settings, key, value)
        
        # For each feature that should be OFF by default, ensure it's OFF in the user settings
        for attr in dir(default_settings):
            if attr.startswith('show_') and not attr.startswith('_'):
                default_value = getattr(default_settings, attr)
                if not default_value:  # If the feature should be OFF by default
                    user_value = getattr(advanced_settings, attr)
                    if user_value:  # But the user has it ON
                        log.debug(f"Turning off {attr} because it should be OFF for {radius_category} field radius")
                        setattr(advanced_settings, attr, False)
        
        # Apply max magnitude limits from default settings
        if hasattr(default_settings, 'hd_max_magnitude') and advanced_settings.hd_max_magnitude is not None:
            if default_settings.hd_max_magnitude is not None:
                advanced_settings.hd_max_magnitude = min(advanced_settings.hd_max_magnitude, default_settings.hd_max_magnitude)
                
        if hasattr(default_settings, 'gcvs_max_magnitude') and advanced_settings.gcvs_max_magnitude is not None:
            if default_settings.gcvs_max_magnitude is not None:
                advanced_settings.gcvs_max_magnitude = min(advanced_settings.gcvs_max_magnitude, default_settings.gcvs_max_magnitude)
                
        if hasattr(default_settings, 'tycho_2_max_magnitude') and advanced_settings.tycho_2_max_magnitude is not None:
            if default_settings.tycho_2_max_magnitude is not None:
                advanced_settings.tycho_2_max_magnitude = min(advanced_settings.tycho_2_max_magnitude, default_settings.tycho_2_max_magnitude)
