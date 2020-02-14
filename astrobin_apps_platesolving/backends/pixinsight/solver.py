import logging

import requests
from django.conf import settings
from django.templatetags.static import get_static_prefix
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
            'moreLayers=VdB|Sharpless|Barnard|PGC',
            'fontsBaseURL=%s' % settings.STATIC_URL + 'astrobin/fonts',
        ]

        observation_time = kwargs.pop('observation_time')
        if observation_time is not None:
            task_params.append('observationTime=%sT00:00:00Z' % observation_time)

        data = {
            'userName': settings.PIXINSIGHT_USERNAME,
            'userPassword': settings.PIXINSIGHT_PASSWORD,
            'taskType': 'ASTROBIN_SVG_OVERLAY',
            'taskParams': '\n'.join(task_params),
            'callbackURL': settings.BASE_URL + reverse('astrobin_apps_platesolution.pixinsight_webhook'),
        }

        r = requests.post(default_url, headers=headers, data=data)

        if r.status_code == 200:
            log.debug("PixInsight plate-solving initiated: %s" % r.text)
            try:
                return r.text.split('\n')[1].split('serialNumber=')[1]
            except IndexError:
                log.error("Unable to parse PixInsight response")
                return None
        else:
            log.error("PixInsight plate-solving could not initiate: %s" % r.text)
