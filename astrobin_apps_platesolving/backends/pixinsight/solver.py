import logging

import requests
from django.conf import settings
from django.urls import reverse

from astrobin.templatetags.tags import thumbnail_scale
from astrobin_apps_platesolving.backends.base import AbstractPlateSolvingBackend

log = logging.getLogger('apps')

default_url = 'https://pixinsight.com/tasks/new-task.php'


class Solver(AbstractPlateSolvingBackend):
    def __init__(self, apiurl=default_url):
        self.session = None
        self.apiurl = apiurl

    def start(self, image_url, **kwargs):
        headers = {
            'content-type': 'application/x-www-form-urlencoded'
        }

        smallSizeRatio = thumbnail_scale(kwargs.pop('image_width'), 'hd', 'regular')

        task_params = [
            'imageURL=%s' % image_url,
            'centerRA=%f' % kwargs.pop('ra'),
            'centerDec=%f' % kwargs.pop('dec'),
            'smallSizeRatio=%f' % smallSizeRatio,
            'imageResolution=%f' % kwargs.pop('pixscale'),
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
        advanced_settings = kwargs.pop('advanced_settings', None)  # type: PlateSolvingAdvancedSettings
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
            if advanced_settings.show_gaia_dr2:
                layers.append('Gaia DR2')
            if advanced_settings.show_ppmxl:
                layers.append('PPMXL')

            if advanced_settings.scaled_font_size == 'S':
                task_params.append('smallSizeTextRatio=%f' % (smallSizeRatio * .85))
                task_params.append('smallSizeStrokeRatio=%f' % (smallSizeRatio * .85))
            elif advanced_settings.scaled_font_size == 'M':
                task_params.append('smallSizeTextRatio=%f' % smallSizeRatio)
                task_params.append('smallSizeStrokeRatio=%f' % smallSizeRatio)
            elif advanced_settings.scaled_font_size == 'L':
                task_params.append('smallSizeTextRatio=%f' % (smallSizeRatio * 1.15))
                task_params.append('smallSizeStrokeRatio=%f' % (smallSizeRatio * 1.15))

        if len(layers) > 0:
            task_params.append('layers=%s' % '|'.join(layers))

        data = {
            'userName': settings.PIXINSIGHT_USERNAME,
            'userPassword': settings.PIXINSIGHT_PASSWORD,
            'taskType': 'ASTROBIN_SVG_OVERLAY',
            'taskParams': '\n'.join(task_params),
            'callbackURL': settings.BASE_URL + reverse('astrobin_apps_platesolution.pixinsight_webhook'),
        }

        log.debug("PixInsight plate-solving: sending request %s" % str(data))

        r = requests.post(default_url, headers=headers, data=data)

        if r.status_code == 200:
            try:
                serial_number = r.text.split('\n')[1].split('serialNumber=')[1]
                log.debug("PixInsight plate-solving initiated: s/n = %s" % serial_number)
                return serial_number
            except IndexError:
                log.error("Unable to parse PixInsight response")
                return None
        else:
            log.error("PixInsight plate-solving could not initiate: %s" % r.text)
