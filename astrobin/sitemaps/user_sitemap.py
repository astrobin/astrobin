from django.contrib.sitemaps import Sitemap

from astrobin.models import UserProfile


class UserSitemap(Sitemap):
    def __init__(self, year, month) -> None:
        super().__init__(UserProfile.objects.all(), year, month)
