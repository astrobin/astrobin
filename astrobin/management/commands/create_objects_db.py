from django.core.management.base import BaseCommand
from astrobin.models import Subject

import csv

class Command(BaseCommand):
    help = "Creates Messier and NGC subjects, using the online Simbad database."

    def handle(self, *args, **options):
        pass
