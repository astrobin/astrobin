from datetime import datetime

from django.db.models import Q

from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd


class IotdService:
    def get_iotds(self):
        return Iotd.objects \
            .filter(date__lte=datetime.now().date(), image__deleted=None) \
            .exclude(image__corrupted=True)

    def get_top_picks(self):
        return Image.objects \
            .exclude(
            Q(iotdvote=None) | Q(corrupted=True)) \
            .filter(
            Q(iotd=None) |
            Q(iotd__date__gt=datetime.now().date())).order_by('-published')
