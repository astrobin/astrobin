import logging
import urllib2

import simplejson
from django.conf import settings


class CloudflareService:
    base_url = "https://api.cloudflare.com/client/v4"

    def __init__(self):
        self.log = logging.getLogger('apps')
        self.token = settings.CLOUDFLARE_TOKEN
        self.zone_id = settings.CLOUDFLARE_ZONE_ID

    def purge_resource(self, path):
        """
        :rtype: None
        :type path: basestring
        """

        if not self.token or not self.zone_id:
            self.log.debug("CloudflareService cannot work without token and zone_id")
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

        request = urllib2.Request(url, data, headers=headers)

        try:
            response = urllib2.urlopen(request).read()

            self.log.debug("Requested to purge Cloudflare cache for file %s" % path)
            self.log.debug(response)
        except urllib2.HTTPError as e:
            self.log.debug("Unable to purge Cloudflare cache for file %s: %s" % (path, e.message))
