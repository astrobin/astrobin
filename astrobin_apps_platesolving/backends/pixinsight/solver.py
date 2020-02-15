import logging

import requests
from django.conf import settings
from django.urls import reverse

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

        task_params = [
            'imageURL=%s' % image_url,
            'centerRA=%f' % kwargs.pop('ra'),
            'centerDec=%f' % kwargs.pop('dec'),
            'imageResolution=%f' % kwargs.pop('pixscale'),
            'moreLayers=VdB|Sharpless|Barnard',
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
