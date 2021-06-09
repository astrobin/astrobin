from datetime import datetime

from astrobin_apps_iotd.models import TopPickNominationsArchive, Iotd, TopPickArchive
from common.services import DateTimeService


class CachingService:
    @staticmethod
    def get_latest_top_pick_nomination_datetime(self):
        try:
            return TopPickNominationsArchive.objects.latest('image__published').image.published
        except TopPickNominationsArchive.DoesNotExist:
            return DateTimeService.now()

    @staticmethod
    def get_latest_top_pick_datetime(self):
        try:
            return TopPickArchive.objects.latest('image__published').image.published
        except TopPickArchive.DoesNotExist:
            return DateTimeService.now()

    @staticmethod
    def get_latest_iotd_datetime(self):
        try:
            return datetime.combine(Iotd.objects.latest('date').date, datetime.min.time())
        except Iotd.DoesNotExist:
            return DateTimeService.now()
