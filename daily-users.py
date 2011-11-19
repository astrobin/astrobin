#!./venv/bin/python

# Run from top directory like this:
# DJANGO_SETTINGS_MODULE="astrobin.settings" ./daily-users.py

from datetime import datetime, timedelta
from django.contrib.auth.models import User
import operator

dates = [x.date_joined.date() for x in User.objects.all()]
reps = {}
for d in dates:
    reps[d] = dates.count(d)

sorted_reps = sorted(reps.iteritems(), key = operator.itemgetter(0))
for r in sorted_reps:
    print "%s: %d" % (str(r[0]), r[1])

