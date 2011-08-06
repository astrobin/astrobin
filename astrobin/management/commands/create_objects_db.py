from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import IntegrityError

from astrobin.models import Subject, SubjectIdentifier

import urllib2
import simplejson


class Command(BaseCommand):
    help = "Creates Messier and NGC subjects, using the online Simbad database."

    def handle(self, *args, **options):
        # WARNING: DO NOT THIS SCRIPT!
        # For some reason, this script will hog the Internet connection;
        # The f file is always closed in the loop, so we're not running
        # out of file descriptos. Still, after the 110 M objects and 16
        # NGC objects, the scripts will hang at urlopen, and no other
        # processes can access the network.
        #
        # See: https://bitbucket.org/siovene/astrobin/issue/59/
        return

        catalogs = {
            'M': 110,
            'NGC': 7840,
        }

        for cat, num in catalogs.iteritems():
            for i in range(1, num):
                print "Fetching information for: %s %d" % (cat, i)
                url = settings.SIMBAD_QUERY_URL + cat + '%20' + str(i)
                json_string = ""
                f = None
                try:
                    f = urllib2.urlopen(url, timeout=3)
                    json_string = f.read()
                except:
                    print "Failed to fetch from Simbad."
                    continue
                try:
                    json = simplejson.loads(json_string)
                except simplejson.JSONDecodeError:
                    # Malformatted query and Simbad didn't accept it. Let's
                    # ignore it
                    print "Failed to parse Simbad's response."
                    f.close()
                    continue

                values = []
                for obj in json:
                    s = Subject()
                    s.initFromJSON(obj)
                    try:
                        s.save()
                    except IntegrityError:
                        # We have it already.
                        s = Subject.objects.get(mainId=obj['mainId'])

                    for id in obj['idlist']:
                        sid = SubjectIdentifier(identifier=id, subject=s)
                        try:
                            sid.save()
                        except IntegrityError:
                            continue

                import pdb; pdb.set_trace()
                f.close()

