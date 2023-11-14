from datetime import datetime

from django.contrib.sitemaps import Sitemap

from astrobin_apps_equipment.models import Accessory


class AccessorySitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return Accessory.objects.all()

    def lastmod(self, obj) -> datetime:
        return getattr(obj, 'updated')

