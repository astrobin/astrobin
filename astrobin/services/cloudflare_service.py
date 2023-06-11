import logging
from typing import List

import requests
import simplejson
from django.conf import settings

log = logging.getLogger(__name__)


class CloudflareService:
    base_url = "https://api.cloudflare.com/client/v4"

    def __init__(self):
        self.token = settings.CLOUDFLARE_TOKEN
        self.zone_id = settings.CLOUDFLARE_ZONE_ID

    def purge_cache(self, paths: List[str]):
        if not self.token or not self.zone_id:
            log.warning("CloudflareService cannot work without token and zone_id")
            return

        if not paths or len(paths) == 0:
            log.warning("CloudflareService cannot purge cache without paths")
            return

        headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json"
        }

        url = "%s/zones/%s/purge_cache" % (self.base_url, self.zone_id)

        data = simplejson.dumps({
            "files": paths
        })

        try:
            requests.post(url, data, headers=headers, timeout=1)
        except Exception as e:
            log.warning("Unable to purge Cloudflare cache for files %s: %s" % (', '.join(paths), str(e)))
