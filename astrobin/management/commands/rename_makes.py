import sys
import difflib

from django.core.management.base import BaseCommand
from django.db.models import Q, Count

from astrobin.models import Gear
from astrobin.utils import unique_items


class Command(BaseCommand):
    help = "Rename makes."

    def handle(self, *args, **options):
        seen = []
        all_makes = sorted(unique_items(Gear.objects.exclude(
            Q(make=None) |
            Q(make='') |
            Q(make__in=seen)).values_list('make', flat=True)))

        print "Total makes: %d." % len(all_makes)

        if args:
            matches = unique_items(difflib.get_close_matches(args[0], all_makes, cutoff = 0.2))
            all_makes = sorted(unique_items(Gear.objects.filter(
                Q(make__in = matches) |
                Q(make__icontains = args[0])).values_list('make', flat = True)))
            print "Restricted to %d makes." % len(all_makes)

        for make in all_makes:
            if make in seen:
                # Should not be necessary, actually.
                continue

            to_update = Gear.objects.filter(make = make)
            count = to_update.count()

            print "[%s]:%d" % (make, count),
            new_make = raw_input("")
            seen.append(make)

            if new_make == '':
                continue

            print "Will update %d items." % count 
            to_update.update(make = new_make)
