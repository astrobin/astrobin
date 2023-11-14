from datetime import datetime

from django.contrib.sitemaps import Sitemap

from astrobin_apps_equipment.models import Camera


class CameraSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return Camera.objects.all()

    def lastmod(self, obj) -> datetime:
        return getattr(obj, 'updated')

