from django.contrib.sitemaps import Sitemap

from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Image


class ImageSitemap(Sitemap):
    def __init__(self, year, month) -> None:
        super().__init__(Image.objects.filter(moderator_decision=ModeratorDecision.APPROVED), year, month)
