# Python
from datetime import datetime

# Django
from django.core.management.base import BaseCommand

# AstroBin
from astrobin.models import ImageOfTheDay
from astrobin_apps_iotd.models import Iotd


class Command(BaseCommand):
    help = "Syncs the new IOTD app to the old models, for API compatibility."

    def handle(self, *args, **options):
        try:
            iotd = Iotd.objects.get(date=datetime.now().date())
            ImageOfTheDay.objects.get_or_create(
                image=iotd.image,
                date=iotd.date,
                chosen_by=iotd.judge)
        except Iotd.DoesNotExist:
            pass
