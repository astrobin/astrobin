import shlex
import difflib
import sys

from django.core.management.base import BaseCommand
from django.db.models import Q

from astrobin.models import Gear
from astrobin.utils import unique_items


class Command(BaseCommand):
    help = "Merges similar make names."

    def handle(self, *args, **options):

        seen = []
        while True:
            number_merged = 0

            queryset = Gear.objects.exclude(Q(make=None) | Q(make='') | Q(make__in=seen))
            all_makes = [x.make for x in Gear.objects.exclude(Q(make=None) | Q(make=''))]

            item = queryset[0]
            matches = unique_items(difflib.get_close_matches(item.make, all_makes))
            if item.make not in seen:
                seen.append(item.make)

            if len(matches) == 1 and matches[0] == item.make:
                continue

            print(item.make)

            for i in range(0, len(matches)):
                if matches[i] != item.make:
                    print('\t%d. %s' % (i, matches[i]))

            to_merge = raw_input("Which ones do I merge [space separated, or q]? ")

            if to_merge == 'q':
                return
            elif to_merge == '':
                continue

            new_make = raw_input("New make name [%s]? " % item.make).decode(sys.stdin.encoding)
            if new_make == '':
                new_make = item.make

            masters = Gear.objects.filter(make=item.make)
            for master in masters:
                master.make = new_make
                master.save()
                number_merged += 1

            for i in shlex.split(to_merge):
                slaves = Gear.objects.filter(make=matches[int(i)])
                for slave in slaves:
                    slave.make = new_make
                    slave.save()
                    number_merged += 1

            print("Merged %d makes." % number_merged)
