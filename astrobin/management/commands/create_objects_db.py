from django.core.management.base import BaseCommand
from astrobin.models import Subject

import csv

class Command(BaseCommand):
    help = "Creates the full list of subjects, using the SAC database."


    def normalized_name(self, name):
        return name.strip().replace(' ', '_')


    def normalized_value(self, value):
        import re
        return re.sub(' +', ' ', value.strip())


    def handle(self, *args, **options):
        data = csv.reader(open('data/SAC_DeepSky_Ver81_QCQ.TXT'))
        fields = data.next()
        for row in data:
            # Zip together the field names and values
            items = zip(fields, row)
            s = None
            try:
                s = Subject.objects.get(OBJECT=self.normalized_name(items[0][1]))
            except Subject.DoesNotExist:
                s = Subject()

            # Add the value to our dictionary
            for (name, value) in items:
                norm_n = self.normalized_name(name)
                norm_v = self.normalized_value(value)

                if norm_v is not None and norm_v != '':
                    print("%s: %s" % (norm_n, norm_v))
                    setattr(s, norm_n, norm_v)

            s.save()
