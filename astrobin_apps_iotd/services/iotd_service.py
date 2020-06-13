from datetime import datetime

from dateutil.utils import today
from django.db.models import Q

from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd


class IotdService:
    def get_iotds(self):
        return Iotd.objects \
            .filter(date__lte=today(), image__deleted=None) \
            .exclude(image__corrupted=True)

    def get_top_picks(self):
        is_iotd = ~Q(iotd=None)
        is_future_iotd = Q(iotd__date__gt=today())
        is_top_pick = ~Q(iotd_votes=None)
        is_corrupted = Q(corrupted=True)

        return Image.objects \
            .filter(Q(~is_iotd | is_future_iotd) & is_top_pick & ~is_corrupted) \
            .order_by('-published')
