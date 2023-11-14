from datetime import datetime

from django.contrib.sitemaps import Sitemap

from astrobin_apps_equipment.models import Telescope


class TelescopeSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return Telescope.objects.all()

    def lastmod(self, obj) -> datetime:
        return getattr(obj, 'updated')

