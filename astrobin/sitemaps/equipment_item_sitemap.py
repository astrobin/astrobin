from datetime import datetime

from django.contrib.sitemaps import Sitemap


class EquipmentItemSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'
    protocol = 'https'

    def __init__(self, model):
        self.model = model

    def items(self):
        return self.model.objects.all()

    def lastmod(self, obj) -> datetime:
        return getattr(obj, 'updated')

    def get_urls(self, page=1, site=None, protocol=None):
        urls = []

        for item in self.paginator.page(page).object_list:
            loc = self.location(item)
            priority = self.priority if self.priority is not None else self.get_priority(item)
            lastmod = self.lastmod(item)
            changefreq = self.changefreq if self.changefreq is not None else self.get_changefreq(item)

            url_info = {
                'location': loc,
                'lastmod': lastmod,
                'changefreq': changefreq,
                'priority': priority
            }

            urls.append(url_info)

        return urls
