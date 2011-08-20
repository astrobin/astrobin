from django.core.management.base import BaseCommand
from django import db

from astrobin.models import Location

import csv
from decimal import Decimal


class Command(BaseCommand):
    help = "Creates database of world cities."

    def handle(self, *args, **options):
        def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
            csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
            for row in csv_reader:
                yield [unicode(cell, 'iso-8859-1') for cell in row]

        reader = unicode_csv_reader(open('data/cities.txt', 'r'))
        # Skip the header:
        reader.next()
        i = 0
        for row in reader:
            print 'Creating city: ' +  row[2]
            l = Location(name=row[2],
                         latitude=Decimal(row[5]),
                         longitude=Decimal(row[6]),
                         user_generated=False)
            l.save()
            i += 1
            if i % 100 == 0:
                db.reset_queries()
