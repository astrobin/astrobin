from models import DeepSky_Acquisition, Image

from django.utils.translation import ugettext as _
from datetime import datetime, timedelta
import time


def daterange(start, end):
    r = (end + timedelta(days=1) - start).days
    return [start + timedelta(days=i) for i in range(r)]


def integration_hours(user, period='monthly'):
    _map = {
        'yearly' : (_("Integration hours, yearly") , '%Y'),
        'monthly': (_("Integration hours, monthly"), '%Y-%m'),
        'daily'  : (_("Integration hours, daily")  , '%Y-%m-%d'),
    }

    flot_label = _map[period][0]
    flot_data = []
    flot_options = {
        'xaxis': {'mode': 'time'},
        'lines': {'show': 'true', 'fill': 'true'},
        'points': {'show': 'true'},
    }

    first = DeepSky_Acquisition.objects.filter(image__user = user).exclude(date = None).order_by('date')
    data = {}
    if first:
        for date in daterange(first[0].date, datetime.today().date()):
            integration = 0
            todays = DeepSky_Acquisition.objects.filter(image__user = user, date = date)
            for i in todays:
                if i.duration and i.number:
                    integration += (i.duration * i.number) / 3600.0
            key = date.strftime(_map[period][1])
            if key in data:
                if integration > 0:
                    data[key] += integration
            else:
                data[key] = integration

        for date, integration in sorted(data.iteritems()):
            flot_data.append([time.mktime(datetime.strptime(date, _map[period][1]).timetuple()) * 1000, integration])

    return (flot_label, flot_data, flot_options)


def uploaded_images(user, period='monthly'):
    _map = {
        'yearly' : (_("Uploaded images, yearly") , '%Y'),
        'monthly': (_("Uploaded images, monthly"), '%Y-%m'),
        'daily'  : (_("Uploaded images, daily")  , '%Y-%m-%d'),
    }

    flot_label = _map[period][0]
    flot_data = []
    flot_options = {
        'xaxis': {'mode': 'time'},
        'lines': {'show': 'true', 'fill': 'true'},
        'points': {'show': 'true'},
    }

    first = Image.objects.filter(user = user).order_by('uploaded')
    data = {}
    if first:
        for date in daterange(first[0].uploaded.date(), datetime.today().date()):
            total = 0
            todays = Image.objects.filter(user = user, uploaded__gte = date, uploaded__lte = date + timedelta(days = 1))
            for i in todays:
                total += 1
            key = date.strftime(_map[period][1])
            if key in data:
                if total > 0:
                    data[key] += total
            else:
                data[key] = total

        for date, total in sorted(data.iteritems()):
            flot_data.append([time.mktime(datetime.strptime(date, _map[period][1]).timetuple()) * 1000, total])

    return (flot_label, flot_data, flot_options)

