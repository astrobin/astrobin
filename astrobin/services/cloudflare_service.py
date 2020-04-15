import logging

import requests
import simplejson
from django.conf import settings

log = logging.getLogger('apps')


class CloudflareService:
    base_url = "https://api.cloudflare.com/client/v4"

    def __init__(self):
        self.token = settings.CLOUDFLARE_TOKEN
        self.zone_id = settings.CLOUDFLARE_ZONE_ID

    def purge_resource(self, path):
        """
        :rtype: None
        :type path: basestring
        """

        if not self.token or not self.zone_id:
            log.debug("CloudflareService cannot work without token and zone_id")
            return

        headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json"
        }

        url = "%s/zones/%s/purge_cache" % (self.base_url, self.zone_id)

        data = simplejson.dumps({
            "files": [
                path
            ]
        })

        try:
            log.debug("Requesting to purge Cloudflare cache for file %s" % path)
            requests.get(url, data, verify=False, headers=headers, timeout=0.5)
        except Exception as e:
            log.warning("Unable to purge Cloudflare cache for file %s: %s" % (path, e.message))
