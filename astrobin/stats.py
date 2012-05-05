from models import DeepSky_Acquisition, Image, UserProfile, Gear, User, Camera, Telescope

from django.utils.translation import ugettext as _
from django.db.models import Q
from django.core.cache import cache

from hitcount.models import Hit

from datetime import datetime, timedelta
import time
import unicodedata
from collections import defaultdict
import operator


def daterange(start, end):
    r = (end + timedelta(days=1) - start).days
    return [start + timedelta(days=i) for i in range(r)]


def integration_hours(user, period = 'monthly', since = 0):
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
        'legend': {
            'position': 'nw',
            'backgroundColor': '#000000',
            'backgroundOpacity': 0.75},
        'grid': {'hoverable': 'true'},
    }

    astrobin = User.objects.get(username = 'astrobin')
    all = DeepSky_Acquisition.objects.all().exclude(date = None).order_by('date')

    if since > 0:
        all = all.filter(date__gte = datetime.today().date() - timedelta(days = since))

    if user != astrobin:
        all = all.filter(image__user = user)
    
    data = {}
    for i in all:
        integration = 0
        if i.duration and i.number:
            integration += (i.duration * i.number) / 3600.0
        key = i.date.strftime(_map[period][1])
        if key in data:
            if integration > 0:
                data[key] += integration
        else:
            data[key] = integration

    if all:
        for date in daterange(all[0].date, datetime.today().date()):
            grouped_date = date.strftime(_map[period][1])
            t = time.mktime(datetime.strptime(grouped_date, _map[period][1]).timetuple()) * 1000
            if grouped_date in data.keys():
                flot_data.append([t, data[grouped_date]])
            else:
                flot_data.append([t, 0])

    return (flot_label, flot_data, flot_options)


def integration_hours_by_gear(user, period='monthly'):
    _map = {
        'yearly' : (_("Integration hours by gear, yearly") , '%Y'),
        'monthly': (_("Integration hours by gear, monthly"), '%Y-%m'),
        'daily'  : (_("Integration hours by gear, daily")  , '%Y-%m-%d'),
    }

    flot_data = []
    flot_options = {
        'xaxis': {'mode': 'time'},
        'lines': {'show': 'true'},
        'points': {'show': 'true'},
        'legend': {
            'noColumns': 3,
        },
        'grid': {'hoverable': 'true'},
    }

    profile = UserProfile.objects.get(user = user)
    all_telescopes = profile.telescopes.all()
    all_cameras = profile.cameras.all()

    thickness = all_telescopes.count() + all_cameras.count()

    for t in (all_telescopes, all_cameras):
        for g in t:
            all = DeepSky_Acquisition.objects.filter(
                Q(image__user = user),
                Q(image__imaging_telescopes = g) | Q(image__imaging_cameras = g)).exclude(date = None).order_by('date')

            g_dict = {
                'label': _map[period][0] + ": " + unicodedata.normalize('NFKD', g.name).encode('ascii', 'ignore'),
                'stage_data': {},
                'data': [],
                'lines': {'lineWidth': thickness},
            }

            for i in all:
                integration = 0
                if i.duration and i.number:
                    integration += (i.duration * i.number) / 3600.0
                key = i.date.strftime(_map[period][1])
                if key in g_dict['stage_data']:
                    g_dict['stage_data'][key] += integration
                else:
                    g_dict['stage_data'][key] = integration

            if all:
                for date in daterange(all[0].date, datetime.today().date()):
                    grouped_date = date.strftime(_map[period][1])
                    t = time.mktime(datetime.strptime(grouped_date, _map[period][1]).timetuple()) * 1000
                    if grouped_date in g_dict['stage_data'].keys():
                        g_dict['data'].append([t, g_dict['stage_data'][grouped_date]])
                    else:
                        g_dict['data'].append([t, 0])

            del g_dict['stage_data']
            flot_data.append(g_dict)
            thickness -= 1

    return (flot_data, flot_options)


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
        'legend': {
            'position': 'nw',
            'backgroundColor': '#000000',
            'backgroundOpacity': 0.75},
        'grid': {'hoverable': 'true'},
    }

    astrobin = User.objects.get(username = 'astrobin')
    all = Image.objects.all().order_by('uploaded')
    if user != astrobin:
        all = all.filter(user = user)

    data = {}
    for i in all:
        key = i.uploaded.date().strftime(_map[period][1])
        if key in data:
            data[key] += 1
        else:
            data[key] = 1 

    if all:
        for date in daterange(all[0].uploaded.date(), datetime.today().date()):
            grouped_date = date.strftime(_map[period][1])
            t = time.mktime(datetime.strptime(grouped_date, _map[period][1]).timetuple()) * 1000
            if grouped_date in data.keys():
                flot_data.append([t, data[grouped_date]])
            else:
                flot_data.append([t, 0])

    return (flot_label, flot_data, flot_options)


def views(user, period='daily'):
    _map = {
        'yearly' : (_("Views, yearly") , '%Y'),
        'monthly': (_("Views, monthly"), '%Y-%m'),
        'daily'  : (_("Views, daily")  , '%Y-%m-%d'),
    }

    flot_label = _map[period][0]
    flot_data = []
    flot_options = {
        'xaxis': {'mode': 'time'},
        'lines': {'show': 'true', 'fill': 'true'},
        'points': {'show': 'true'},
        'legend': {
            'position': 'nw',
            'backgroundColor': '#000000',
            'backgroundOpacity': 0.75},
        'grid': {'hoverable': 'true'},
    }

    user_images = Image.objects.filter(user = user)
    all = Hit.objects.filter(hitcount__object_pk__in = [x.pk for x in user_images]).order_by('created')
    data = {}
    for i in all:
        key = i.created.date().strftime(_map[period][1])
        if key in data:
            data[key] += 1
        else:
            data[key] = 1 

    if all:
        for date in daterange(all[0].created.date(), datetime.today().date()):
            grouped_date = date.strftime(_map[period][1])
            t = time.mktime(datetime.strptime(grouped_date, _map[period][1]).timetuple()) * 1000
            if grouped_date in data.keys():
                flot_data.append([t, data[grouped_date]])
            else:
                flot_data.append([t, 0])

    return (flot_label, flot_data, flot_options)


def image_views(image_id, period='daily'):
    _map = {
        'yearly' : (_("Views, yearly") , '%Y'),
        'monthly': (_("Views, monthly"), '%Y-%m'),
        'daily'  : (_("Views, daily")  , '%Y-%m-%d'),
    }

    flot_label = _map[period][0]
    flot_data = []
    flot_options = {
        'xaxis': {'mode': 'time'},
        'lines': {'show': 'true', 'fill': 'true'},
        'points': {'show': 'true'},
        'legend': {
            'position': 'nw',
            'backgroundColor': '#000000',
            'backgroundOpacity': 0.75},
        'grid': {'hoverable': 'true'},
    }

    all = Hit.objects.filter(hitcount__object_pk = image_id).order_by('created')
    data = {}
    for i in all:
        key = i.created.date().strftime(_map[period][1])
        if key in data:
            data[key] += 1
        else:
            data[key] = 1 

    if all:
        for date in daterange(all[0].created.date(), datetime.today().date()):
            grouped_date = date.strftime(_map[period][1])
            t = time.mktime(datetime.strptime(grouped_date, _map[period][1]).timetuple()) * 1000
            if grouped_date in data.keys():
                flot_data.append([t, data[grouped_date]])
            else:
                flot_data.append([t, 0])

    return (flot_label, flot_data, flot_options)


def subject_images_monthly(subject_id):
    flot_label = _("Uploaded images, monthly")
    flot_data = []
    flot_options = {
        'bars': {
            'show': 'true',
            'fill': 'true',
            'barWidth': 0.9,
            'align': 'center',
        },
        'legend': {
            'show': False,
        },
        'grid': {'hoverable': 'true'},
    }

    all = Image.objects.filter(subjects__id = subject_id).order_by('uploaded')
    data = {}
    for i in all:
        key = i.uploaded.date().strftime('%m')
        if key in data:
            data[key] += 1
        else:
            data[key] = 1 

    if all:
        for date in daterange(all[0].uploaded.date(), datetime.today().date()):
            grouped_date = date.strftime('%m')
            if grouped_date in data.keys():
                flot_data.append([grouped_date, data[grouped_date]])
            else:
                flot_data.append([grouped_date, 0])

    return (flot_label, flot_data, flot_options)


def subject_integration_monthly(subject_id):
    flot_label = _("Integration hours, monthly")
    flot_data = []
    flot_options = {
        'bars': {
            'show': 'true',
            'fill': 'true',
            'barWidth': 0.9,
            'align': 'center',
        },
        'legend': {
            'show': False,
        },
        'grid': {'hoverable': 'true'},
    }

    all = DeepSky_Acquisition.objects \
        .filter(image__subjects__id = subject_id) \
        .exclude(Q(number = None) | Q(duration = None) | Q(date = None)) \
        .order_by('date')

    data = {}
    for i in all:
        key = i.date.strftime('%m')
        if key in data:
            data[key] += (i.number * i.duration / 3600.00)
        else:
            data[key] = 0

    if all:
        for date in daterange(all[0].date, datetime.today().date()):
            grouped_date = date.strftime('%m')
            if grouped_date in data.keys():
                flot_data.append([grouped_date, data[grouped_date]])
            else:
                flot_data.append([grouped_date, 0])

    return (flot_label, flot_data, flot_options)


def subject_total_images(subject_id):
    period = 'monthly'
    _map = {
        'monthly': (_("Total images"), '%Y-%m'),
    }

    flot_label = _map[period][0]
    flot_data = []
    flot_options = {
        'xaxis': {'mode': 'time'},
        'lines': {'show': 'true', 'fill': 'true'},
        'points': {'show': 'true'},
        'legend': {
            'position': 'nw',
            'backgroundColor': '#000000',
            'backgroundOpacity': 0.75},
        'grid': {'hoverable': 'true'},
    }

    all = Image.objects.filter(subjects__id = subject_id).order_by('uploaded')

    data = {}
    total = 0
    for i in all:
        key = i.uploaded.date().strftime(_map[period][1])
        if key in data:
            total += 1
            data[key] = total
        else:
            total += 1
            data[key] = total

    if all:
        for date in daterange(all[0].uploaded.date(), datetime.today().date()):
            grouped_date = date.strftime(_map[period][1])
            t = time.mktime(datetime.strptime(grouped_date, _map[period][1]).timetuple()) * 1000
            if grouped_date in data.keys():
                flot_data.append([t, data[grouped_date]])
            else:
                flot_data.append([t, 0])

    return (flot_label, flot_data, flot_options)


def subject_camera_types(subject_id, lang = 'en'):
    flot_label = None 
    flot_data = []
    flot_options = {
        'series': {
            'pie': {
                'show': True,
            },
        },
        'legend': {
            'show': True,
            'container': '#stats_camera_types_legend',
        },
        'grid': {
            'hoverable': True,
        },
    }

    cache_key = 'stats.subjects.camera_types.%d.%s' % (int(subject_id), lang)
    if not cache.has_key(cache_key):
        all = Image.objects.all() \
                           .exclude(imaging_cameras__type = None) \
                           .order_by('uploaded')

        if subject_id != '0':
            all = all.filter(subjects__id = subject_id)

        data = {}
        for i in all:
            for c in i.imaging_cameras.all():
                key = unicode(Camera.CAMERA_TYPES[c.type][1])
                if key in data:
                    data[key] += 1
                else:
                    data[key] = 1

        for label, value in data.iteritems():
            flot_data.append({'label': label, 'data': value * 100.0 / all.count()})

        flot_data = cache.set(cache_key, flot_data, 7*24*60*60)
    else:
        flot_data = cache.get(cache_key)

    return (flot_label, flot_data, flot_options)


def subject_telescope_types(subject_id, lang='en'):
    flot_label = None 
    flot_data = []
    flot_options = {
        'series': {
            'pie': {
                'show': True,
            },
        },
        'legend': {
            'show': True,
            'container': '#stats_telescope_types_legend',
        },
        'grid': {
            'hoverable': True,
        },
    }

    cache_key = 'stats.subjects.telescope_types.%d.%s' % (int(subject_id), lang)
    if not cache.has_key(cache_key):
        all = Image.objects.all() \
                           .exclude(imaging_telescopes__type = None) \
                           .order_by('uploaded')

        if subject_id != '0':
            all = all.filter(subjects__id = subject_id)

        data = {}
        for i in all:
            for c in i.imaging_telescopes.all():
                key = unicode(Telescope.TELESCOPE_TYPES[c.type][1])
                if key in data:
                    data[key] += 1
                else:
                    data[key] = 1

        for label, value in data.iteritems():
            flot_data.append({'label': label, 'data': value * 100.0 / all.count()})

        flot_data = cache.set(cache_key, flot_data, 7*24*60*60)
    else:
        flot_data = cache.get(cache_key)

    return (flot_label, flot_data, flot_options)


def camera_types_trend():
    period = 'monthly'
    _map = {
        'monthly': (_("Integration hours by camera type"), '%Y-%m'),
    }

    flot_data = []
    flot_options = {
        'xaxis': {'mode': 'time'},
        'lines': {'show': 'true'},
        'legend': {
            'position': 'nw',
            'backgroundColor': '#000000',
            'backgroundOpacity': 0.75,
        },
        'grid': {
            'hoverable': True,
        },
    }

    for g in Camera.CAMERA_TYPES:
        if g[0] > 1: 
            # Limit to CCD and DSLR
            continue

        all = DeepSky_Acquisition.objects \
            .filter(Q(image__imaging_cameras__type = g[0]) & Q(date__gte = '2011-01-01')) \
            .exclude(date = None) \
            .order_by('date')

        g_dict = {
            'label': unicode(g[1]),
            'stage_data': {},
            'data': [],
        }

        for i in all:
            integration = 0
            if i.duration and i.number:
                integration += (i.duration * i.number) / 3600.0
            key = i.date.strftime(_map[period][1])
            if key in g_dict['stage_data']:
                g_dict['stage_data'][key] += integration
            else:
                g_dict['stage_data'][key] = integration

        if all:
            for date in daterange(all[0].date, datetime.today().date()):
                grouped_date = date.strftime(_map[period][1])
                t = time.mktime(datetime.strptime(grouped_date, _map[period][1]).timetuple()) * 1000
                if grouped_date in g_dict['stage_data'].keys():
                    g_dict['data'].append([t, g_dict['stage_data'][grouped_date]])
                else:
                    g_dict['data'].append([t, 0])

        del g_dict['stage_data']
        flot_data.append(g_dict)

    return (flot_data, flot_options)


def telescope_types_trend():
    period = 'monthly'
    _map = {
        'monthly': (_("Integration hours by camera type"), '%Y-%m'),
    }

    flot_data = []
    flot_options = {
        'xaxis': {'mode': 'time'},
        'lines': {'show': 'true'},
        'legend': {
            'show': True,
            'position': 'nw',
            'backgroundColor': '#000000',
            'backgroundOpacity': 0.75,
        },
        'grid': {
            'hoverable': True,
        }
    }

    telescope_types = {
        _('Refractor'): range(0, 6),
        _('Reflector'): range(6, 12),
        _('Catadioptric'): range(12, 21),
        _('Camera lens'): [21,],
    }
    for key, value in telescope_types.items():
        filters = reduce(operator.or_, [Q(**{'image__imaging_telescopes__type': x}) for x in value])
        all = DeepSky_Acquisition.objects \
            .filter(filters & Q(date__gte = '2011-01-01')) \
            .order_by('date')

        g_dict = {
            'label': key,
            'stage_data': {},
            'data': [],
        }

        for i in all:
            integration = 0
            if i.duration and i.number:
                integration += (i.duration * i.number) / 3600.0
            key = i.date.strftime(_map[period][1])
            if key in g_dict['stage_data']:
                g_dict['stage_data'][key] += integration
            else:
                g_dict['stage_data'][key] = integration

        if all:
            for date in daterange(all[0].date, datetime.today().date()):
                grouped_date = date.strftime(_map[period][1])
                t = time.mktime(datetime.strptime(grouped_date, _map[period][1]).timetuple()) * 1000
                if grouped_date in g_dict['stage_data'].keys():
                    g_dict['data'].append([t, g_dict['stage_data'][grouped_date]])
                else:
                    g_dict['data'].append([t, 0])

        del g_dict['stage_data']
        flot_data.append(g_dict)

    return (flot_data, flot_options)

