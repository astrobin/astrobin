from django.core.management.base import BaseCommand
from astrobin.models import Subject

import csv

class Command(BaseCommand):
    help = "Creates the full list of subjects, using the SAC database."

    def handle(self, *args, **options):
        data = csv.reader(open('data/SAC_DeepSky_Ver81_QCQ.TXT'))
        fields = data.next()
        for row in data:
            print("Creating data for: %s" % row[0])
            s = Subject()
            # Zip together the field names and values  
            items = zip(fields, row)  
            # Add the value to our dictionary  
            for (name, value) in items:  
                setattr(s, name, value.strip())
            s.save()
