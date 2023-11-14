from datetime import datetime

from django.contrib.sitemaps import Sitemap

from astrobin_apps_equipment.models import Filter


class FilterSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return Filter.objects.all()

    def lastmod(self, obj) -> datetime:
        return getattr(obj, 'updated')

