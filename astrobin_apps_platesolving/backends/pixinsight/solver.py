import logging
import random
import string
import urllib

from django.conf import settings

from astrobin.templatetags.tags import thumbnail_scale
from astrobin_apps_platesolving.backends.base import AbstractPlateSolvingBackend
from astrobin_apps_platesolving.models import PlateSolvingAdvancedTask

log = logging.getLogger('apps')


class Solver(AbstractPlateSolvingBackend):
    def start(self, image_url, **kwargs):
        advanced_settings = kwargs.pop('advanced_settings', None)  # type: PlateSolvingAdvancedSettings
        image_width = kwargs.pop('image_width')  # type: int
        image_height = kwargs.pop('image_height')  # type: int
        smallSizeRatio = thumbnail_scale(image_width, 'hd', 'regular')  # type: float
        pixscale = kwargs.pop('pixscale')  # type: float
        hd_width = min(image_width, settings.THUMBNAIL_ALIASES['']['hd']['size'][0])  # type: int
        hd_ratio = max(1, image_width / float(hd_width))  # type: float
        hd_height = int(image_height / hd_ratio)  # type: int
        settings_hd_width = settings.THUMBNAIL_ALIASES['']['hd']['size'][0]

        if image_width > settings_hd_width and advanced_settings and not advanced_settings.sample_raw_frame_file:
            ratio = image_width / float(settings_hd_width)
            pixscale = float(pixscale) * ratio

        task_params = [
            'imageURL=%s' % image_url,
            'centerRA=%f' % kwargs.pop('ra'),
            'centerDec=%f' % kwargs.pop('dec'),
            'largeSize=%d' % max(hd_width, hd_height),
            'smallSizeRatio=%f' % smallSizeRatio,
            'imageResolution=%f' % pixscale,
            'fontsBaseURL=%s' % settings.STATIC_URL + 'astrobin/fonts',
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
            if advanced_settings.show_constellation_borders:
                layers.append('Constellation Borders')
            if advanced_settings.show_constellation_lines:
                layers.append('Constellation Lines')
            if advanced_settings.show_named_stars:
                layers.append('NamedStars')
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

        task = PlateSolvingAdvancedTask.objects.create(
            serial_number=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32)),
            task_params=urllib.quote('\n'.join(task_params)),
        )

        log.debug("PixInsight plate-solving: created task %s" % task.serial_number)
        return task.serial_number
