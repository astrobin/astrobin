from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        # List of static view names for which you want to generate sitemap entries
        return ['index', 'pybb:index', 'top_pick_nominations', 'top_picks', 'iotd_archive',]

    def location(self, item):
        return reverse(item)
