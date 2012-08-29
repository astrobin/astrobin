from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.generic.list_detail import object_list
from django.views.generic.list_detail import object_detail
from django.views.generic.create_update import create_object
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse
from django.core.exceptions import MultipleObjectsReturned, ValidationError
from django.conf import settings
from django.template import RequestContext
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.db import IntegrityError
from django.utils.translation import ugettext as _
from django.forms.models import formset_factory, inlineformset_factory
from django.utils.functional import curry
from django.utils.encoding import smart_str, smart_unicode
from django.utils.hashcompat import md5_constructor
from django.utils.http import urlquote

from haystack.query import SearchQuerySet, SQ
import persistent_messages
from djangoratings.models import Vote
from reviews.forms import ReviewedItemForm
from actstream.models import Action
from registration.forms import RegistrationForm

from uuid import uuid4
import os
import simplejson
import csv
import flickrapi
import urllib2
from datetime import datetime, date, timedelta
import operator
import re
import unicodedata

from models import *
from forms import *
from management import NOTICE_TYPES
from notifications import *
from notification.models import NoticeSetting, NOTICE_MEDIA_DEFAULTS
from shortcuts import *
from tasks import *
from search_indexes import xapian_escape
from image_utils import make_image_of_the_day
from gear import *
from utils import *

import settings
import pytz

# need to translate to a non-naive timezone, even if timezone == settings.TIME_ZONE, so we can compare two dates
def to_user_timezone(date, profile):
    timezone = profile.timezone if profile.timezone else settings.TIME_ZONE               
    return date.replace(tzinfo=pytz.timezone(settings.TIME_ZONE)).astimezone(pytz.timezone(timezone))
    
def to_system_timezone(date, profile):
    timezone = profile.timezone if profile.timezone else settings.TIME_ZONE               
    return date.replace(tzinfo=pytz.timezone(timezone)).astimezone(pytz.timezone(settings.TIME_ZONE))
    
def now_timezone():   
    return datetime.datetime.now().replace(tzinfo=pytz.timezone(settings.TIME_ZONE)).astimezone(pytz.timezone(settings.TIME_ZONE))


def monthdelta(date, delta):
    m, y = (date.month+delta) % 12, date.year + ((date.month)+delta-1) // 12
    if not m: m = 12
    d = [31,
         29 if y%4==0 and not y%400==0 else 28,
         31,30,31,30,31,31,30,31,30,31][m-1]
    return date.replace(day=d,month=m, year=y)

def valueReader(source, field):
    def unicode_truncate(s, length, encoding='utf-8'):
        encoded = s.encode(encoding)[:length]
        return encoded.decode(encoding, 'ignore')

    def utf_8_encoder(data):
        for line in data:
            yield line.encode('utf-8')

    as_field = 'as_values_' + field
    value = ''
    if as_field in source:
        value += source[as_field]
    if field in source:
        value += ',' + source[field]
        
    if not (as_field in source or field in source):
        return [], ""

    items = []
    reader = csv.reader(utf_8_encoder([value]),
                        skipinitialspace = True)
    for row in reader:
        items += [unicode_truncate(unicode(x, 'utf-8'), 64) for x in row if x != '']

    return items, value


def get_or_create_location(prop, value):
    k = None
    created = False

    try:
        return Location.objects.get(id=value)
    except ValueError:
        pass

    try:
        k, created = Location.objects.get_or_create(**{prop : value})
    except MultipleObjectsReturned:
        k = Location.objects.filter(**{prop : value})[0]

    if created:
        k.user_generated = True
        k.save()

    return k



def jsonDump(all):
    if len(all) > 0:
        return simplejson.dumps([{'id': i.id, 'name': i.get_name(), 'complete': is_gear_complete(i.id)} for i in all])
    else:
        return []


def jsonDumpSubjects(all):
    if len(all) > 0:
        return simplejson.dumps([{'id': i.id, 'name': i.mainId} for i in all])
    else:
        return []


# VIEWS

def index(request):
    """Main page"""
    response_dict = {
        'small_size': settings.SMALL_THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'global_actions': Action.objects.all()[:16],
        'registration_form': RegistrationForm(),
    }

    profile = None
    if request.user.is_authenticated():
        profile = UserProfile.objects.get(user=request.user)

        response_dict['recent_from_followees'] = \
            Image.objects.filter(is_stored = True, is_wip = False, user__in = profile.follows.all())[:10]

        response_dict['recently_favorited'] = \
            Image.objects.annotate(last_favorited = models.Max('favorite__created')) \
                         .exclude(last_favorited = None) \
                         .order_by('-last_favorited')[:10]

        recent_fives_list = []
        l = 0
        while len(recent_fives_list) < 10:
            recent_fives_qs = \
                Image.objects.filter(votes__score = 5) \
                             .distinct() \
                             .order_by('-votes__date_added')[l:l+10]
            for i in recent_fives_qs:
                if i not in recent_fives_list:
                    recent_fives_list.append(i)
            l += 1
        response_dict['recently_five_starred'] = recent_fives_list[:10]

        iotd = ImageOfTheDay.objects.all()[0]
        gear_list = (
            ('Imaging telescopes or lenses', iotd.image.imaging_telescopes.all(), 'imaging_telescopes'),
            ('Imaging cameras'   , iotd.image.imaging_cameras.all(), 'imaging_cameras'),
            ('Mounts'            , iotd.image.mounts.all(), 'mounts'),
            ('Guiding telescopes or lenses', iotd.image.guiding_telescopes.all(), 'guiding_telescopes'),
            ('Guiding cameras'   , iotd.image.guiding_cameras.all(), 'guiding_cameras'),
            ('Focal reducers'    , iotd.image.focal_reducers.all(), 'focal_reducers'),
            ('Software'          , iotd.image.software.all(), 'software'),
            ('Filters'           , iotd.image.filters.all(), 'filters'),
            ('Accessories'       , iotd.image.accessories.all(), 'accessories'),
        )

        response_dict['image_of_the_day'] = iotd
        response_dict['gear_list'] = gear_list

    return object_list(
        request, 
        queryset = Image.objects.filter(is_stored = True, is_wip = False).order_by('-uploaded'),
        template_name = 'index.html',
        template_object_name = 'image',
        paginate_by = 10 if request.user.is_authenticated() else 16,
        extra_context = response_dict)


@require_GET
def expore_choose(request):
    return render_to_response(
        'explore_choose.html', {}, 
        context_instance = RequestContext(request))


@require_GET
def wall(request):
    """The Big Wall"""
    sqs = SearchQuerySet().all().models(Image)

    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
    }

    if request.GET.get('sort') == '-acquired':
        response_dict['sort'] = '-acquired'
        sqs = sqs.order_by('-last_acquisition_date')
    elif request.GET.get('sort') == '-views':
        response_dict['sort'] = '-views'
        sqs = sqs.order_by('-views');
    elif request.GET.get('sort') == '-rating':
        response_dict['sort'] = '-rating'
        sqs = sqs.order_by('-rating', '-votes')
    elif request.GET.get('sort') == '-favorited':
        response_dict['sort'] = '-favorited'
        sqs = sqs.order_by('-favorited')
    elif request.GET.get('sort') == '-integration':
        response_dict['sort'] = '-integration'
        sqs = sqs.order_by('-integration')
    elif request.GET.get('sort') == '-comments':
        response_dict['sort'] = '-comments'
        sqs = sqs.order_by('-comments')
    else:
        response_dict['sort'] = '-uploaded'
        sqs = sqs.order_by('-uploaded')

    filter = request.GET.get('filter')
    if filter:
        response_dict['filter'] = filter
    if filter == 'all_ds':
        sqs = sqs.filter(is_deep_sky = True)
    elif filter == 'clusters':
        sqs = sqs.filter(is_clusters = True)
    elif filter == 'nebulae':
        sqs = sqs.filter(is_nebulae = True)
    elif filter == 'galaxies':
        sqs = sqs.filter(is_galaxies = True)
    elif filter == 'all_ss':
        sqs = sqs.filter(is_solar_system = True)
    elif filter == 'sun':
        sqs = sqs.filter(is_sun = True)
    elif filter == 'moon':
        sqs = sqs.filter(is_moon = True)
    elif filter == 'planets':
        sqs = sqs.filter(is_planets = True)
    elif filter == 'comets':
        sqs = sqs.filter(is_comets = True)
    elif filter == 'wide':
        sqs = sqs.filter(subject_type = 300)
    elif filter == 'trails':
        sqs = sqs.filter(subject_type = 400)
    elif filter == 'gear':
        sqs = sqs.filter(subject_type = 500)
    elif filter == 'other':
        sqs = sqs.filter(subject_type = 600)

    return object_list(
        request, 
        queryset=sqs,
        template_name='wall.html',
        template_object_name='image',
        paginate_by = 100,
        extra_context = response_dict)


def popular(request):
    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,

        'min_lat': 0,
        'max_lat': 90,
        'hem': 'B',

        'months': [],
        'has_previous': None,
    }

    all_images = []
    min_lat = request.GET.get('min_lat') if 'min_lat' in request.GET else 0
    max_lat = request.GET.get('max_lat') if 'max_lat' in request.GET else 90
    hem = request.GET.get('hem') if 'hem' in request.GET else 'B'

    response_dict['min_lat'] = min_lat
    response_dict['max_lat'] = max_lat
    response_dict['hem'] = hem

    variables = [min_lat, max_lat, hem, request.LANGUAGE_CODE]
    hash = md5_constructor(u':'.join([urlquote(var) for var in variables]))
    cache_key = 'template.cache.%s.%s' % ('popular_monthly', hash.hexdigest())

    if not cache.has_key(cache_key):
        ignore_list = (
            'Moon',
            'Luna',
            'Jupiter',
            'Mars',

            'M42', # mispelled

            'M 32',
            'M 43',
            'M 110',

            'CCDM J05408-0156AB',
            '* 43 Ori',
            '* iot Ori',
            '* del Ori a',
            'V* eps Ori',

            'NGC 1432', # Nebulosity in M45
            'NGC 1435', # Nebulosity in M45
            'NGC 1976a', # Part of Orion nebula
            'NGC 1976b', # Part of Orion nebula
            'NGC 1976c', # Part of Orion nebula
            'NGC 1973',
            'NGC 1975',
            'NGC 1977',
            'NGC 1980',
            'NGC 1981',
            'NGC 1990',
            'NGC 2023',
            'NGC 2024',
            'NGC 2237',
            'NGC 2252',
            'NGC 5195',
            'NGC 6350', # cluster in M8
            'NGC 6997', # cluster in NGC7000

            'IC 431',
            'IC 432',
            'IC 435',

            'NAME ALNILAM A',
            'NAME TAYGETA',
            'NAME ELECTRA',
            'NAME ATLAS',
            'NAME PLEIONE',
            'NAME CELENO',
            'NAME MEROPE',
        )


        for month in range(1, 13):
            fake_date = datetime.datetime(1970, month, 1, 0, 0, 0)
            subject_filters = Q(image__acquisition__date__month = month) | \
                              Q(image__locations__lat_deg__gte = min_lat) |  \
                              Q(image__locations__lat_deg__lte = max_lat)
            if hem != 'B':
                subject_filters = subject_filters & \
                              Q(image__locations__lat_side = hem)

            subjects = Subject.objects \
                .filter(subject_filters) \
                .exclude(reduce(operator.or_, [Q(**{'mainId': x}) for x in ignore_list])) \
                .annotate(popularity=Count('image')) \
                .order_by('-popularity')[:10]

            images = []
            for subject in subjects:
                subjects_images = Image.objects \
                        .filter(subjects__mainId = subject.mainId) \
                        .order_by('-rating_score')

                for subjects_image in subjects_images:
                    pk = subjects_image.pk
                    if not images or (pk not in images and pk not in all_images):
                        images.append(pk)
                        all_images.append(pk) # don't care about order here
                        break

            if images:
                filters = reduce(operator.or_, [Q(**{'pk': x}) for x in images])
                images_sqs = Image.objects.filter(filters)
                response_dict['months'].append((fake_date, subjects, reversed(images_sqs)))

    return render_to_response(
        'most_popular.html',
        response_dict,
        context_instance = RequestContext(request))
    

@require_GET
def messier(request):
    """Messier marathon"""

    queryset = MessierMarathon.objects.all().order_by('messier_number')
    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
    }

    return object_list(
        request, 
        queryset=queryset,
        template_name='messier_marathon.html',
        template_object_name='object',
        paginate_by = 55, # Haha, how clever.
        extra_context = response_dict)


@require_GET
@login_required
def messier_nomination(request, id):
    image = get_object_or_404(Image, pk=id)

    response_dict = {
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'image': image,
        'has_messier': False,
        'has_multiple_messier': False,
        'messier_object': None,
        'messier_objects_list': [],
        'form': None,
    }

    subjects = image.subjects.all()
    messier = [x.name for x in subjects if x.catalog == 'M']
    if not messier:
        pass
    elif len(messier) == 1:
        response_dict['has_messier'] = True
        response_dict['messier_object'] = messier[0]
    else:
        response_dict['has_messier'] = True
        response_dict['has_multiple_messier'] = True
        response_dict['form'] = MultipleMessierForm(messier)

    return render_to_response(
        'messier_nomination.html',
        response_dict,
        context_instance = RequestContext(request))


@require_POST
@login_required
def messier_nomination_process(request):
    image = get_object_or_404(Image, pk=request.POST['image_id'])
    messier_object = request.POST['messier_object']

    response_dict = {
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'image': image,
        'already_nominated': False,
    }

    nominations, created = MessierMarathonNominations.objects.get_or_create(
        messier_number = int(messier_object),
        image = image)
    if nominations.nominators.filter(id = request.user.id):
        response_dict['already_nominated'] = True
    else:
        top_for_object = MessierMarathonNominations.objects.filter(messier_number = int(messier_object)).order_by('-nominations')[:1]
        top_nominations = top_for_object[0].nominations if top_for_object else 0

        nominations.nominators.add(request.user)
        nominations.nominations += 1
        nominations.save()

        push_notification(
            [image.user], 'messier_nomination',
            {
                'user': request.user.username,
                'user_url': request.user.get_absolute_url(),
                'messier_object': 'M %s' % messier_object,
                'image_url': image.get_absolute_url(),
            },
        )

        if nominations.nominations > top_nominations:
            try:
                marathon_item = MessierMarathon.objects.get(messier_number = int(messier_object))
                marathon_item.image = image
            except MessierMarathon.DoesNotExist:
                marathon_item = MessierMarathon(messier_number = int(messier_object), image = image)
            finally:
                marathon_item.save()
                push_notification(
                    [image.user], 'messier_top_nomination',
                    {
                        'messier_object': 'M %s' % messier_object,
                        'image_url': image.get_absolute_url(),
                    },
                )

    return render_to_response(
        'messier_nomination_finish.html',
        response_dict,
        context_instance = RequestContext(request))


@require_GET
def fits(request):
    qs = Image.objects.exclude(Q(link_to_fits = None) | Q(link_to_fits = ''))

    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
    }

    return object_list(
        request, 
        queryset=qs,
        template_name='fits.html',
        template_object_name='image',
        paginate_by = 20,
        extra_context = response_dict)


@require_GET
def no_javascript(request):
    return render_to_response('no_javascript.html',
        context_instance=RequestContext(request))


@require_GET
def image_detail(request, id, r):
    """ Show details of an image"""
    image = get_object_or_404(Image, pk=id)

    def missing_revision(image):
        messages.warning(request, _("The revision you are looking for is invalid, or was deleted. This is the original image."))
        return HttpResponseRedirect(image.get_absolute_url())

    is_revision = False
    revision_id = 0
    revision_image = None
    revisions = ImageRevision.objects.filter(image=image)
    is_final = image.is_final
    is_ready = image.is_stored

    if 'r' in request.GET:
        r = request.GET.get('r')

    if r and r != '0':
        is_revision = True
        try:
            revision_id = int(r)
        except ValueError:
            try:
                revision_image = ImageRevision.objects.get(image = image, label = r)
            except ImageRevision.DoesNotExist:
                return missing_revision(image)
        if not revision_image:
            try:
                revision_image = ImageRevision.objects.get(image = image, id = revision_id)
            except ImageRevision.DoesNotExist:
                return missing_revision(image)

        is_final = revision_image.is_final
        is_ready = revision_image.is_stored
    elif not r:
        if not is_final:
            final_revs = revisions.filter(is_final = True)
            # We should only have one
            if final_revs:
                final = revisions.filter(is_final = True)[0]
                return HttpResponseRedirect('/%i/%s/' % (image.id, final.label))

    from moon import MoonPhase;

    already_voted = bool(image.rating.get_rating_for_user(request.user, request.META['REMOTE_ADDR']))
    votes = image.rating.votes
    score = image.rating.score
    rating = float(score)/votes if votes > 0 else 0

    related = None
    related_images = None
    if 'related' in request.GET:
        related = request.GET['related']
    else:
        related = 'rel_user'

    related_images = SearchQuerySet().models(Image)
    if related == 'rel_user':
        related_images = related_images.filter(username__exact=image.user.username)
    elif related == 'rel_subject':
        subjects = [xapian_escape(s.mainId) for s in image.subjects.all()]
        related_images = related_images.filter(SQ(subjects__in=subjects))
    elif related == 'rel_imaging_telescope':
        telescopes = [xapian_escape(t.get_name()) for t in image.imaging_telescopes.all()]
        related_images = related_images.filter(SQ(imaging_telescopes__in=telescopes))
    elif related == 'rel_imaging_camera':
        cameras = [xapian_escape(c.get_name()) for c in image.imaging_cameras.all()]
        related_images = related_images.filter(SQ(imaging_cameras__in=cameras))

    related_images = related_images.exclude(django_id=id).order_by('-uploaded')

    gear_list = (
        ('Imaging telescopes or lenses', image.imaging_telescopes.all(), 'imaging_telescopes'),
        ('Imaging cameras'   , image.imaging_cameras.all(), 'imaging_cameras'),
        ('Mounts'            , image.mounts.all(), 'mounts'),
        ('Guiding telescopes or lenses', image.guiding_telescopes.all(), 'guiding_telescopes'),
        ('Guiding cameras'   , image.guiding_cameras.all(), 'guiding_cameras'),
        ('Focal reducers'    , image.focal_reducers.all(), 'focal_reducers'),
        ('Software'          , image.software.all(), 'software'),
        ('Filters'           , image.filters.all(), 'filters'),
        ('Accessories'       , image.accessories.all(), 'accessories'),
    )
    gear_list_has_commercial = False
    gear_list_has_paid_commercial = False
    for g in gear_list:
        if g[1].exclude(commercial = None).count() > 0:
            gear_list_has_commercial = True
            break
    for g in gear_list:
        for i in g[1].exclude(commercial = None):
            if i.commercial.is_paid() or i.commercial.producer == request.user:
                gear_list_has_paid_commercial = True
                # It would be faster if we exited the outer loop, but really,
                # how many gear items can an image have?
                break

    deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=image)
    ssa = None
    image_type = None
    deep_sky_data = {}

    try:
        ssa = SolarSystem_Acquisition.objects.get(image=image)
    except:
        pass

    if deep_sky_acquisitions:
        image_type = 'deep_sky'

        moon_age_list = []
        moon_illuminated_list = []
        acquisitions = []

        dsa_data = {
            'dates': [],
            'frames': {},
            'integration': 0,
            'darks': [],
            'flats': [],
            'flat_darks': [],
            'bias': [],
            'bortle': [],
            'mean_sqm': [],
            'mean_fwhm': [],
            'temperature': [],
        }
        for a in deep_sky_acquisitions:
            if a.date is not None and a.date not in dsa_data['dates']:
                dsa_data['dates'].append(a.date)
                m = MoonPhase(a.date)
                moon_age_list.append(m.age)
                moon_illuminated_list.append(m.illuminated * 100.0)

            if a.number and a.duration:
                key = ""
                if a.filter:
                    key = "filter(%s)" % a.filter.get_name()
                if a.iso:
                    key += '-ISO(%d)' % a.iso 
                if a.sensor_cooling:
                    key += '-temp(%d)' % a.sensor_cooling
                if a.binning:
                    key += '-bin(%d)' % a.binning
                key += '-duration(%d)' % a.duration

                try:
                    current_frames = dsa_data['frames'][key]['integration']
                except KeyError:
                    current_frames = '0x0"'

                integration_re = re.match(r'^(\d+)x(\d+)"$', current_frames)
                current_number = int(integration_re.group(1))
                current_duration = int(integration_re.group(2))

                dsa_data['frames'][key] = {}
                dsa_data['frames'][key]['filter_url'] = a.filter.get_absolute_url() if a.filter else '#'
                dsa_data['frames'][key]['filter'] = a.filter if a.filter else ''
                dsa_data['frames'][key]['iso'] = 'ISO%d' % a.iso if a.iso else ''
                dsa_data['frames'][key]['sensor_cooling'] = '%dC' % a.sensor_cooling if a.sensor_cooling else ''
                dsa_data['frames'][key]['binning'] = 'bin %sx%s' % (a.binning, a.binning) if a.binning else ''
                dsa_data['frames'][key]['integration'] = '%sx%s"' % (current_number + a.number, a.duration)

                dsa_data['integration'] += (a.duration * a.number / 3600.0)

            for i in ['darks', 'flats', 'flat_darks', 'bias']:
                if a.filter and getattr(a, i):
                    dsa_data[i].append("%d" % getattr(a, i))
                elif getattr(a, i):
                    dsa_data[i].append(getattr(a, i))

            if a.bortle:
                dsa_data['bortle'].append(a.bortle)

            if a.mean_sqm:
                dsa_data['mean_sqm'].append(a.mean_sqm)

            if a.mean_fwhm:
                dsa_data['mean_fwhm'].append(a.mean_fwhm)

            if a.temperature:
                dsa_data['temperature'].append(a.temperature)

        def average(values):
            if not len(values):
                return 0
            return float(sum(values)) / len(values)

        frames_list = sorted(dsa_data['frames'].items())

        deep_sky_data = (
            (_('Resolution'), '%dx%d' % (image.w, image.h) if (image.w and image.h) else None),
            (_('Dates'), sorted(dsa_data['dates'])),
            (_('Locations'), u', '.join([x.name for x in image.locations.all()])),
            (_('Frames'),
                ('\n' if len(frames_list) > 1 else '') +
                u'\n'.join("%s %s" % (
                    "<a href=\"%s\">%s</a>:" % (f[1]['filter_url'], f[1]['filter']) if f[1]['filter'] else '',
                    "%s %s %s %s" % (f[1]['integration'], f[1]['iso'], f[1]['sensor_cooling'], f[1]['binning']),
                ) for f in frames_list)),
            (_('Integration'), "%.1f %s" % (dsa_data['integration'], _("hours"))),
            (_('Darks'), '~%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['darks'])) / len(dsa_data['darks'])) if dsa_data['darks'] else 0),
            (_('Flats'), '~%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['flats'])) / len(dsa_data['flats'])) if dsa_data['flats'] else 0),
            (_('Flat darks'), '~%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['flat_darks'])) / len(dsa_data['flat_darks'])) if dsa_data['flat_darks'] else 0),
            (_('Bias'), '~%d' % (int(reduce(lambda x, y: int(x) + int(y), dsa_data['bias'])) / len(dsa_data['bias'])) if dsa_data['bias'] else 0),
            (_('Avg. Moon age'), ("%.2f " % (average(moon_age_list), ) + _("days")) if moon_age_list else None),
            (_('Avg. Moon phase'), "%.2f%%" % (average(moon_illuminated_list), ) if moon_illuminated_list else None),
            (_('Bortle Dark-Sky Scale'), "%.2f" % (average([float(x) for x in dsa_data['bortle']])) if dsa_data['bortle'] else None),
            (_('Mean SQM'), "%.2f" % (average([float(x) for x in dsa_data['mean_sqm']])) if dsa_data['mean_sqm'] else None),
            (_('Mean FWHM'), "%.2f" % (average([float(x) for x in dsa_data['mean_fwhm']])) if dsa_data['mean_fwhm'] else None),
            (_('Temperature'),
             "%.2f" % (average([float(x) for x in dsa_data['temperature']])) if dsa_data['temperature'] else None),
        )

    elif ssa:
        image_type = 'solar_system'

    follows = False
    profile = None
    if request.user.is_authenticated():
        profile = UserProfile.objects.get(user=request.user)
    if profile:
        if UserProfile.objects.get(user=image.user) in profile.follows.all():
            follows = True

    uploaded_on = to_user_timezone(image.uploaded, profile) if profile else image.uploaded

    resized_size = settings.RESIZED_IMAGE_SIZE
    if is_revision:
        if revision_image.w > 0 and revision_image.w < resized_size:
            resized_size = revision_image.w
    else:
        if image.w > 0 and image.w < resized_size:
            resized_size = image.w

    subjects = image.subjects.all()
    subjects_limit = 5 

    licenses = (
        (0, 'cc/c.png',           LICENSE_CHOICES[0][1]),
        (1, 'cc/cc-by-nc-sa.png', LICENSE_CHOICES[1][1]),
        (2, 'cc/cc-by-nc.png',    LICENSE_CHOICES[2][1]),
        (3, 'cc/cc-by-nc-nd.png', LICENSE_CHOICES[3][1]),
        (4, 'cc/cc-by.png',       LICENSE_CHOICES[4][1]),
        (5, 'cc/cc-by-sa.png',    LICENSE_CHOICES[5][1]),
        (6, 'cc/cc-by-nd.png',    LICENSE_CHOICES[6][1]),
    )

    solved_ext = ''
    if image.uploaded < datetime.datetime(2011, 11, 13, 5, 3, 1):
        solved_ext = '.png'
    elif image.plot_is_overlay:
        solved_ext = '.png'
    else:
        solved_ext = image.original_ext

    preferred_language = UserProfile.objects.get(user = image.user).language
    if preferred_language:
        preferred_language = LANGUAGES[preferred_language]
    else:
        preferred_language = _("English")

    response_dict = {'s3_url': settings.S3_URL,
                     'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
                     'small_thumbnail_size': settings.SMALL_THUMBNAIL_SIZE,
                     'resized_size': resized_size,
                     'already_voted': already_voted,
                     'current_rating': "%.2f" % rating,
                     'votes_number': votes,
                     'related': related,
                     'related_images': related_images,
                     'gear_list': gear_list,
                     'gear_list_has_commercial': gear_list_has_commercial,
                     'gear_list_has_paid_commercial': gear_list_has_paid_commercial,
                     'image_type': image_type,
                     'ssa': ssa,
                     'deep_sky_data': deep_sky_data,
                     'mod': request.GET.get('mod') if 'mod' in request.GET else '',
                     'inverted': True if 'mod' in request.GET and request.GET['mod'] == 'inverted' else False,
                     'solved': True if 'mod' in request.GET and request.GET['mod'] == 'solved' else False,
                     'follows': follows,
                     'private_message_form': PrivateMessageForm(),
                     'upload_revision_form': ImageRevisionUploadForm(),
                     'revisions': revisions,
                     'is_revision': is_revision,
                     'revision_image': revision_image,
                     'is_ready': is_ready,
                     'is_final': is_final,
                     'full': 'full' in request.GET,
                     'dates_label': _("Dates"),
                     'uploaded_on': uploaded_on,
                     'subjects_short': subjects[:subjects_limit],
                     'subjects_reminder': subjects[subjects_limit:],
                     'subjects_all': subjects,
                     'subjects_limit': subjects_limit,
                     'subject_type': [x[1] for x in Image.SUBJECT_TYPE_CHOICES if x[0] == image.subject_type][0] if image.subject_type else 0,
                     'license_icon': licenses[image.license][1],
                     'license_title': licenses[image.license][2],
                     # Because of a regression introduced at
                     # revision e1dad12babe5, now we have to
                     # implement this ugly hack.
                     'solved_ext': solved_ext,

                     'solar_system_main_subject_id': image.solar_system_main_subject,
                     'solar_system_main_subject': SOLAR_SYSTEM_SUBJECT_CHOICES[image.solar_system_main_subject][1] if image.solar_system_main_subject is not None else None,
                     'comment_form': CommentForm(),
                     'comments': Comment.objects.filter(image = image),
                     'preferred_language': preferred_language,
                     'already_favorited': Favorite.objects.filter(image = image, user = request.user).count() > 0 if request.user.is_authenticated() else False,
                     'times_favorited': Favorite.objects.filter(image = image).count(),
                     'plot_overlay_left' : (settings.RESIZED_IMAGE_SIZE - image.w) / 2 if image.w < settings.RESIZED_IMAGE_SIZE else 0,
                    }

    return object_detail(
        request,
        queryset = Image.objects.all(),
        object_id = id,
        template_name = 'image/detail.html',
        template_object_name = 'image',
        extra_context = response_dict)


@require_GET
def image_full(request, id, r):
    image = get_object_or_404(Image, pk=id)

    is_revision = False
    revision_id = 0
    revision_image = None
    if 'r' in request.GET:
        r = request.GET.get('r')

    if r and r != '0':
        is_revision = True
        try:
            revision_id = int(r)
        except ValueError:
            revision_image = get_object_or_404(ImageRevision, image = image, label = r)
        if not revision_image:
            revision_image = get_object_or_404(ImageRevision, id=revision_id)

    return object_detail(
        request,
        queryset = Image.objects.all(),
        object_id = id,
        template_name = 'image/full.html',
        template_object_name = 'image',
        extra_context = {
            's3_url': settings.S3_URL,
            'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
            'revision_image': revision_image,
            'is_revision': is_revision,
            'real': 'real' in request.GET,
        })


@require_GET
def image_get_rating(request, image_id):
    image = get_object_or_404(Image, pk=image_id)
    votes = image.rating.votes
    score = image.rating.score
    rating = float(score)/votes if votes > 0 else 0

    response_dict = {'rating': '%.2f' % rating}
    return ajax_response(response_dict)


@login_required
def image_upload(request):
    """Create new image"""
    response_dict = {}

    profile = None
    if request.user.is_authenticated():
        profile = UserProfile.objects.get(user=request.user)
        if profile and profile.telescopes.all() and profile.cameras.all():
            response_dict['upload_form'] = ImageUploadForm()

    return render_to_response(
        "upload.html",
        response_dict,
        context_instance=RequestContext(request))


@login_required
@require_POST
def image_upload_process(request):
    """Process the form"""
    def upload_error():
        messages.error(request, _("Invalid image or no image provided. Allowed formats are JPG, PNG and GIF."))
        return HttpResponseRedirect('/upload/')

    if 'file' not in request.FILES:
        return upload_error()

    form = ImageUploadForm(request.POST, request.FILES)
    file = request.FILES["file"]
    filename, original_ext = str(uuid4()), os.path.splitext(file.name)[1]
    original_ext = original_ext.lower()
    if original_ext == '.jpeg':
        original_ext = '.jpg'
    if original_ext not in ('.jpg', '.png', '.gif'):
        return upload_error()

    try:
        from PIL import Image as PILImage
        trial_image = PILImage.open(file)
        trial_image.verify()
    except:
        return upload_error()

    destination = open(settings.UPLOADS_DIRECTORY + filename + original_ext, 'wb+')
    for chunk in file.chunks():
        destination.write(chunk)
    destination.close()

    profile = UserProfile.objects.get(user = request.user)
    image = Image(
        filename=filename,
        original_ext=original_ext,
        user=request.user,
        license = profile.default_license,
        is_wip = 'wip' in request.POST)

    image.save()

    return HttpResponseRedirect("/edit/presolve/%d/" % image.id)


@login_required
def image_edit_presolve(request, id):
    image = get_object_or_404(Image, pk = id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = ImageEditPresolveForm(data=request.POST, instance=image)
        if form.is_valid():
            form.save()

            if image.is_stored:
                image.solve()

            done_later = 'done_later' in request.POST
            if done_later:
                if image.presolve_information > 1:
                    messages.info(request, _("Plate-solving has started in the background. It might take a while, so please don't request it again! You will be notified when the job has completed. Thanks!"))

                return HttpResponseRedirect(image.get_absolute_url());

            return HttpResponseRedirect('/edit/watermark/%s/' % image.id)
    else:
        form = ImageEditPresolveForm(instance=image)

    return render_to_response('image/edit/presolve.html',
        {
            'image': image,
             'form': form,
        },
        context_instance = RequestContext(request))


@login_required
@require_GET
def image_edit_basic(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    subjects =  u', '.join(x.mainId for x in image.subjects.all())

    form = ImageEditBasicForm(user = image.user, instance = image)

    return render_to_response('image/edit/basic.html',
        {'image':image,
         's3_url':settings.S3_URL,
         'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
         'form':form,
         'prefill_dict': {
            'subjects': [jsonDumpSubjects(image.subjects.all()),
                         "",
                         _("No results. Sorry."),
                         _("Click on a suggestion or press TAB to add what you typed")],
         },
         'is_ready': image.is_stored,
         'subjects': subjects,
        },
        context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_watermark(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user or image.is_stored:
        return HttpResponseForbidden()

    profile = UserProfile.objects.get(user = image.user)
    if not profile.default_watermark_text or profile.default_watermark_text == '':
        profile.default_watermark_text = "Copyright %s" % image.user.username
        profile.save()

    image.watermark = profile.default_watermark
    image.watermark_text = profile.default_watermark_text
    image.watermark_position = profile.default_watermark_position
    image.watermark_opacity = profile.default_watermark_opacity

    form = ImageEditWatermarkForm(instance = image)

    return render_to_response('image/edit/watermark.html',
        {
            'image': image,
            'form': form,
        },
        context_instance = RequestContext(request))


@login_required
@require_GET
def image_edit_gear(request, id):
    image = Image.objects.get(pk=id)
    profile = UserProfile.objects.get(user=image.user)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    no_gear = True
    if profile.telescopes and profile.cameras:
        no_gear = False

    form = ImageEditGearForm(user=image.user, instance=image)
    response_dict = {
        'form': form,
        's3_url':settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'is_ready':image.is_stored,
        'image':image,
        'no_gear':no_gear,
        'copy_gear_form': CopyGearForm(request.user),
    }

    return render_to_response('image/edit/gear.html',
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_acquisition(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    dsa_qs = DeepSky_Acquisition.objects.filter(image=image)
    solar_system_acquisition = None

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=image)
    except:
        pass

    if dsa_qs:
        edit_type = 'deep_sky'
    elif solar_system_acquisition:
        edit_type = 'solar_system'
    elif 'edit_type' in request.REQUEST:
       edit_type = request.REQUEST['edit_type']
    else:
       edit_type = None

    deep_sky_acquisition_formset = None
    deep_sky_acquisition_basic_form = None
    advanced = False
    if edit_type == 'deep_sky' or image.is_solved:
        advanced = dsa_qs[0].advanced if dsa_qs else False
        advanced = request.GET['advanced'] if 'advanced' in request.GET else advanced
        advanced = True if advanced == 'true' else advanced
        advanced = False if advanced == 'false' else advanced
        if advanced:
            extra = 0
            if 'add_more' in request.GET:
                extra = 1
            if not dsa_qs:
                extra = 1
            DSAFormSet = inlineformset_factory(Image, DeepSky_Acquisition, extra=extra, can_delete=False, form=DeepSky_AcquisitionForm)
            profile = UserProfile.objects.get(user=image.user)
            filter_queryset = profile.filters.all()
            DSAFormSet.form = staticmethod(curry(DeepSky_AcquisitionForm, queryset = filter_queryset))
            deep_sky_acquisition_formset = DSAFormSet(instance=image)
        else:
            dsa = dsa_qs[0] if dsa_qs else DeepSky_Acquisition({image: image, advanced: False})
            deep_sky_acquisition_basic_form = DeepSky_AcquisitionBasicForm(instance=dsa)

    response_dict = {
        'image': image,
        'edit_type': edit_type,
        'ssa_form': SolarSystem_AcquisitionForm(instance = solar_system_acquisition),
        'deep_sky_acquisitions': deep_sky_acquisition_formset,
        'deep_sky_acquisition_basic_form': deep_sky_acquisition_basic_form,
        'advanced': advanced,
        'solar_system_acquisition': solar_system_acquisition,
        's3_url':settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'is_ready':image.is_stored,
    }

    return render_to_response('image/edit/acquisition.html',
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_acquisition_reset(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    DeepSky_Acquisition.objects.filter(image=image).delete()
    SolarSystem_Acquisition.objects.filter(image=image).delete()

    response_dict = {
        'image': image,
        's3_url':settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'is_ready':image.is_stored,
        'deep_sky_acquisition_basic_form': DeepSky_AcquisitionBasicForm(),
    }
    return render_to_response('image/edit/acquisition.html',
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_make_final(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    revisions = ImageRevision.objects.filter(image = image)
    for r in revisions:
        r.is_final = False
        r.save()
    image.is_final = True
    image.save()

    return HttpResponseRedirect('/%i/' % image.id)


@login_required
@require_GET
def image_edit_revision_make_final(request, id):
    r = get_object_or_404(ImageRevision, pk=id)
    if request.user != r.image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    other = ImageRevision.objects.filter(image = r.image)
    for i in other:
        i.is_final = False
        i.save()

    r.image.is_final = False
    r.image.save()

    r.is_final = True
    r.save()

    return HttpResponseRedirect('/%i/%s/' % (r.image.id, r.label))


@login_required
@require_GET
def image_edit_license(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    form = ImageLicenseForm(instance = image)
    return render_to_response(
        'image/edit/license.html',
        {'form': form,
         'image': image},
        context_instance = RequestContext(request))


@login_required
@require_POST
def image_edit_save_basic(request):
    def find_subject(id):
        def find_in_simbad(id):
            import simbad
            subject = simbad.find_single_subject(id.strip())
            if subject:
                return subject
            else:
                subjects = simbad.find_subjects(id.strip())
                if subjects:
                    return subjects[0]

        try:
            return Subject.objects.get(id = float(id))
        except ValueError:
            subject = Subject.objects.filter(Q(mainId = id) | Q(name = id))
            if subject:
               return subject[0]
            else:
                identifier = SubjectIdentifier.objects.filter(identifier = id)
                if identifier:
                    return identifier[0].subject
                else:
                    subject = find_in_simbad(id)
                    if subject:
                        return subject
        except Subject.DoesNotExist:
            return None

        '''Alright fine, I give up. Let's look for it in
        our database.'''
        subject = Subject()
        subject.oid = -999
        subject.mainId = id.strip()
        subject.save()

        return subject

    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)
    form = ImageEditBasicForm(user = image.user, data=request.POST, instance=image)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if not form.is_valid():
        subjects =  u', '.join(x.mainId for x in image.subjects.all())

        response_dict = {
            'image': image,
            's3_url': settings.S3_URL,
            'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
            'form': form,
            'prefill_dict': {
               'subjects': [jsonDumpSubjects(image.subjects.all()),
                            "",
                            _("No results. Sorry.")],
            },
            'is_ready': image.is_stored,
            'subjects': subjects,
        }

        return render_to_response("image/edit/basic.html",
            response_dict,
            context_instance=RequestContext(request))

    prefill_dict = {}

    try:
        form.save()
    except ValueError:
        pass

    image.subjects.clear()
    (ids, value) = valueReader(request.POST, 'subjects')
    for id in ids:
        subject = find_subject(id)
        if subject:
            image.subjects.add(subject)
    prefill_dict['subjects'] = [jsonDumpSubjects(image.subjects.all()),
                                "",
                                _("No results. Sorry.")]
    image.save()

    if 'was_not_ready' in request.POST:
        if 'submit_next' in request.POST and 'skip_rest' not in request.POST:
            return HttpResponseRedirect('/edit/gear/%i/' % image.id)

        image.process(image.presolve_information > 1)
        return HttpResponseRedirect(image.get_absolute_url())

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect('/edit/basic/%i/' % image.id)


@login_required
@require_POST
def image_edit_save_watermark(request):
    image_id = request.POST.get('image_id')
    image = get_object_or_404(Image, pk=image_id)
    if request.user != image.user or image.is_stored:
        return HttpResponseForbidden()

    form = ImageEditWatermarkForm(data = request.POST, instance = image)
    if not form.is_valid():
        return render_to_response(
            'image/edit/watermark.html',
            {
                'image': image,
                'form': form,
            },
            context_instance = RequestContext(request))

    form.save()

    # Save defaults in profile
    profile = UserProfile.objects.get(user = image.user)
    profile.default_watermark = form.cleaned_data['watermark']
    profile.default_watermark_text = form.cleaned_data['watermark_text']
    profile.default_watermark_position = form.cleaned_data['watermark_position']
    profile.default_watermark_opacity = form.cleaned_data['watermark_opacity']
    profile.save()

    if 'submit_next' in request.POST:
        return HttpResponseRedirect('/edit/basic/%i/' % image.id)

    image.process(image.presolve_information > 1)
    return HttpResponseRedirect(image.get_absolute_url())


@login_required
@require_POST
def image_edit_save_gear(request):
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)
    profile = UserProfile.objects.get(user = image.user)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    image.imaging_telescopes.clear()
    image.guiding_telescopes.clear()
    image.mounts.clear()
    image.imaging_cameras.clear()
    image.guiding_cameras.clear()
    image.focal_reducers.clear()
    image.filters.clear()
    image.software.clear()
    image.accessories.clear()

    form = ImageEditGearForm(data=request.POST,
                             user=image.user,
                             instance=image)
    response_dict = {
        'image': image,
        's3_url':settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'is_ready':image.is_stored,
    }

    if not form.is_valid():
        return render_to_response("image/edit/gear.html",
            response_dict,
            context_instance=RequestContext(request))
    form.save()

    response_dict['image'] = image

    if 'was_not_ready' in request.POST:
        if 'submit_next' in request.POST:
            return HttpResponseRedirect('/edit/acquisition/%i/' % image.id)

        if not image.is_stored:
            image.process(image.presolve_information > 1)

        return HttpResponseRedirect(image.get_absolute_url())

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect('/edit/gear/%i/' % image.id)


@login_required
@require_POST
def image_edit_save_acquisition(request):
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    edit_type = request.POST.get('edit_type')
    advanced = request.POST['advanced'] if 'advanced' in request.POST else False
    advanced = True if advanced == 'true' else False

    response_dict = {
        'image': image,
        'edit_type': edit_type,
        's3_url':settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'is_ready':image.is_stored,
    }

    dsa_qs = DeepSky_Acquisition.objects.filter(image=image)
    solar_system_acquisition = None

    for a in SolarSystem_Acquisition.objects.filter(image=image):
        a.delete()

    if edit_type == 'deep_sky' or image.is_solved:
        if advanced:
            DSAFormSet = inlineformset_factory(Image, DeepSky_Acquisition, can_delete=False, form=DeepSky_AcquisitionForm)
            saving_data = {}
            for i in request.POST:
                saving_data[i] = request.POST[i]
            saving_data['advanced'] = advanced
            deep_sky_acquisition_formset = DSAFormSet(saving_data, instance=image)
            response_dict['deep_sky_acquisitions'] = deep_sky_acquisition_formset
            response_dict['advanced'] = True
            if deep_sky_acquisition_formset.is_valid():
                deep_sky_acquisition_formset.save()
                if 'add_more' in request.POST:
                    DSAFormSet = inlineformset_factory(Image, DeepSky_Acquisition, extra=1, can_delete=False, form=DeepSky_AcquisitionForm)
                    profile = UserProfile.objects.get(user=image.user)
                    filter_queryset = profile.filters.all()
                    DSAFormSet.form = staticmethod(curry(DeepSky_AcquisitionForm, queryset = filter_queryset))
                    deep_sky_acquisition_formset = DSAFormSet(instance=image)
                    response_dict['deep_sky_acquisitions'] = deep_sky_acquisition_formset
                    response_dict['next_acquisition_session'] = deep_sky_acquisition_formset.total_form_count() - 1
                    if not dsa_qs:
                        messages.info(request, _("Fill in one session, before adding more."))
                    return render_to_response('image/edit/acquisition.html',
                        response_dict,
                        context_instance=RequestContext(request))
            else:
                return render_to_response('image/edit/acquisition.html',
                                          response_dict,
                                          context_instance=RequestContext(request))
        else:
            DeepSky_Acquisition.objects.filter(image=image).delete()
            dsa = DeepSky_Acquisition()
            dsa.image = image
            deep_sky_acquisition_basic_form = DeepSky_AcquisitionBasicForm(data=request.POST, instance=dsa)
            if deep_sky_acquisition_basic_form.is_valid():
                deep_sky_acquisition_basic_form.save()
            else:
                response_dict['deep_sky_acquisition_basic_form'] = deep_sky_acquisition_basic_form
                return render_to_response('image/edit/acquisition.html',
                                          response_dict,
                                          context_instance=RequestContext(request))

    elif edit_type == 'solar_system':
        ssa =  SolarSystem_Acquisition(image = image)
        form = SolarSystem_AcquisitionForm(data = request.POST, instance = ssa)
        response_dict['ssa_form'] = form
        if not form.is_valid():
            response_dict['ssa_form'] = form
            return render_to_response('image/edit/acquisition.html',
                                      response_dict,
                                      context_instance=RequestContext(request))
        form.save()

    if 'was_not_ready' in request.POST and 'add_mode' not in request.POST:
        image.process(image.presolve_information > 1)
        return HttpResponseRedirect(image.get_absolute_url())

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect("/edit/acquisition/%s/" % image_id)


@login_required
@require_POST
def image_edit_save_license(request):
    image_id = request.POST.get('image_id')
    image = get_object_or_404(Image, pk=image_id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    form = ImageLicenseForm(data = request.POST, instance = image)
    if not form.is_valid():
        return render_to_response(
            'image/edit/license.html',
            {'form': form,
             'image': image},
            context_instance = RequestContext(request))

    form.save()

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect('/edit/license/%s/' % image_id)

@login_required
@require_GET
def image_delete(request, id):
    image = get_object_or_404(Image, pk=id) 
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    image.delete()
    push_notification([request.user], 'image_deleted', {});

    return HttpResponseRedirect("/");


@login_required
@require_GET
def image_delete_revision(request, id):
    revision = get_object_or_404(ImageRevision, pk=id) 
    image = revision.image
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if revision.is_final:
        image.is_final = True
        image.save()

    revision.delete()

    return HttpResponseRedirect("/%i/" % image.id);


@login_required
@require_GET
def image_delete_original(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    revisions = ImageRevision.objects.filter(image = image).order_by('-uploaded')
    final = None
    if revisions:
        for r in revisions:
            if r.is_final:
                final = r
        if not final:
            # Fallback to the most recent revision.
            final = revisions[0]
    else:
        # You can't delete just the original if you have no revisions.
        return HttpResponseForbidden()

    image.filename = final.filename
    image.original_ext = final.original_ext
    image.uploaded = final.uploaded

    image.w = final.w
    image.h = final.h

    image.is_stored = final.is_stored
    image.is_solved = False # We don't solve revisions.

    image.is_final = True
    image.was_revision = True

    image.save()
    final.delete(dont_delete_data = True)

    # Update ImageOfTheDay
    today = date.today()
    try:
        iotd = ImageOfTheDay.objects.get(date = today, image = image)
        make_image_of_the_day(image)
    except ImageOfTheDay.DoesNotExist:
        pass

    return HttpResponseRedirect("/%i/" % image.id);


@login_required
@require_GET
def image_promote(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if image.is_wip:
        image.is_wip = False
        image.save()

        followers = [x.from_userprofile.user
                     for x in
                     UserProfile.follows.through.objects.filter(
                        to_userprofile = request.user)]
        push_notification(followers, 'new_image',
            {
                'originator': request.user,
                'object_url': settings.ASTROBIN_BASE_URL + image.get_absolute_url()
            })


    return HttpResponseRedirect('/%i/' % image.id);


@login_required
@require_GET
def image_demote(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if not image.is_wip:
        image.is_wip = True
        image.save()

    return HttpResponseRedirect('/%i/' % image.id);


@login_required
@require_GET
def me(request):
    return HttpResponseRedirect('/users/%s/%s' % (request.user.username, '?staging' if 'staging' in request.GET else ''))


@require_GET
def user_page(request, username):
    """Shows the user's public page"""
    user = get_object_or_404(User, username = username)
    profile = UserProfile.objects.get(user=user)

    follows = False
    viewer_profile = None
    if request.user.is_authenticated():
        viewer_profile = UserProfile.objects.get(user=request.user)
    if viewer_profile:
        if UserProfile.objects.get(user=user) in viewer_profile.follows.all():
            follows = True

    section = 'public'
    subsection = request.GET.get('sub')
    if not subsection:
        subsection = 'year'
    subtitle = None
    backlink = None

    smart_albums = []
    sqs = Image.objects.filter(user = user, is_stored = True).order_by('-uploaded')
    lad_sql = 'SELECT date FROM astrobin_acquisition '\
              'WHERE date IS NOT NULL AND image_id = astrobin_image.id '\
              'ORDER BY date DESC '\
              'LIMIT 1'

    if 'staging' in request.GET:
        if request.user != user:
            return HttpResponseForbidden()
        sqs = sqs.filter(is_wip = True)
        section = 'staging'
    else:
        sqs = sqs.filter(is_wip = False)
        if subsection == 'uploaded':
            # All good already
            pass
        elif subsection == 'acquired':
            sqs = sqs.extra(select = {'last_acquisition_date': lad_sql},
                            order_by = ['-last_acquisition_date'])
        elif subsection == 'year':
            if 'year' in request.GET:
                year = request.GET.get('year')
                try:
                    year = int(year)
                    sqs = sqs.filter(acquisition__date__year = year).extra(
                        select = {'last_acquisition_date': lad_sql},
                        order_by = ['-last_acquisition_date']
                    ).distinct()
                except ValueError:
                    sqs = Image.objects.none()

                subtitle = year
                backlink = "?public&sub=year"
            else:
                acq = Acquisition.objects.filter(image__user = user)
                years = sorted(list(set([a.date.year for a in acq if a.date])), reverse = True)

                k_list = [] 
                smart_albums.append(k_list)

                for y in years:
                    k_dict = {str(y): {'message': None, 'images': []}}
                    k_list.append(k_dict)
                    for i in sqs.filter(acquisition__date__year = y).extra(
                        select = {'last_acquisition_date': lad_sql},
                        order_by = ['-last_acquisition_date']
                    ).distinct():
                        k_dict[str(y)]['images'].append(i)

                l = _("No date specified")
                k_dict = {l: {'message': None, 'images': []}}
                k_dict[l]['message'] = _("To fill in the missing dates, use the <strong>Edit acquisition details</strong> entry in the <strong>Actions</strong> menu for each image.")
                k_list.append(k_dict)
                for i in sqs.filter(
                    Q(subject_type__lt = 500) &
                    (Q(acquisition = None) | Q(acquisition__date = None))).distinct():
                    k_dict[l]['images'].append(i)
               
                sqs = Image.objects.none()
        elif subsection == 'gear':
            from templatetags.tags import gear_name

            if 'gear' in request.GET:
                try:
                    gear = int(request.GET.get('gear'))
                except ValueError:
                    # Probably the Google bot is following some old links, from the time when
                    # the 'gear' argument was the name of the gear item.
                    raise Http404

                sqs = sqs.filter(Q(imaging_telescopes__id = gear) | Q(imaging_cameras__id = gear))

                try:
                    subtitle = gear_name(Gear.objects.get(id=gear))
                except Gear.DoesNotExist:
                    subtitle = ''

                backlink = "?public&sub=gear"
            else:
                k_list = []
                smart_albums.append(k_list)
                for qs, filter in {
                    profile.telescopes.all(): 'imaging_telescopes',
                    profile.cameras.all(): 'imaging_cameras',
                }.iteritems():
                    for k in qs:
                        name = gear_name(k)
                        k_dict = {name: {'message': None, 'images': []}}
                        k_list.append(k_dict)
                        for i in sqs.filter(**{filter: k}).distinct():
                            k_dict[name]['images'].append(i)

                l = _("No imaging telescopes or lenses, or no imaging cameras specified")
                k_dict = {l: {'message': None, 'images': []}}
                k_dict[l]['message'] = _("To fill in the missing gear, use the <strong>Edit gear used</strong> entry in the <strong>Actions</strong> menu for each image.")
                k_list.append(k_dict)
                for i in sqs.filter(Q(imaging_telescopes = None) | Q(imaging_cameras = None)).distinct():
                    k_dict[l]['images'].append(i)

                l = _("Gear images")
                k_dict = {l: {'message': None, 'images': []}}
                k_list.append(k_dict)
                for i in sqs.filter(Q(subject_type = 500)).distinct():
                    k_dict[l]['images'].append(i)

                sqs = Image.objects.none()
        elif subsection == 'subject':
            def reverse_subject_type(label):
                ret = []
                for key, value in SUBJECT_TYPES.iteritems():
                    if value == label:
                        ret.append(key)
                return ret

            if 'subject' in request.GET:
                subject_type = request.GET.get('subject')
                r = reverse_subject_type(subject_type)
                sqs = sqs.filter(Q(subjects__otype__in = r)).distinct()
                subtitle = subject_type
                backlink = "?public&sub=subject"
            else:
                k_list = []
                smart_albums.append(k_list)

                for l in SUBJECT_LABELS.values():
                    k_dict = {l: {'message': None, 'images': []}}
                    k_list.append(k_dict)
                    r = reverse_subject_type(l)
                    for i in sqs.filter(Q(subjects__otype__in = r)).distinct():
                        k_dict[l]['images'].append(i)

                l = _("Solar system")
                k_dict = {l: {'message': None, 'images': []}}
                k_list.append(k_dict)
                for i in sqs.filter(solar_system_main_subject__gte = 0):
                    k_dict[l]['images'].append(i)

                l = _("Extremely wide field")
                k_dict = {l: {'message': None, 'images': []}}
                k_list.append(k_dict)
                for i in sqs.filter(subject_type = 300):
                    k_dict[l]['images'].append(i)

                l = _("Star trails")
                k_dict = {l: {'message': None, 'images': []}}
                k_list.append(k_dict)
                for i in sqs.filter(subject_type = 400):
                    k_dict[l]['images'].append(i)

                l = _("Gear")
                k_dict = {l: {'message': None, 'images': []}}
                k_list.append(k_dict)
                for i in sqs.filter(subject_type = 500):
                    k_dict[l]['images'].append(i)

                l = _("Other")
                k_dict = {l: {'message': None, 'images': []}}
                k_list.append(k_dict)
                for i in sqs.filter(subject_type = 600):
                    k_dict[l]['images'].append(i)

                l = _("No subjects specified")
                k_dict = {l: {'message': None, 'images': []}}
                k_dict[l]['message'] = _("To fill in the missing subjects, use the <strong>Edit basic information</strong> entry in the <strong>Actions</strong> menu for each image.")
                k_list.append(k_dict)
                for i in sqs.filter(
                    (Q(subject_type = 100) | Q(subject_type = 200)) &
                    (Q(subjects = None)) &
                    (Q(solar_system_main_subject = None))).distinct():

                    k_dict[l]['images'].append(i)

                sqs = Image.objects.none()
        elif subsection == 'nodata':
            k_list = []
            smart_albums.append(k_list)

            l = _("No subjects specified")
            k_dict = {l: {'message': None, 'images': []}}
            k_dict[l]['message'] = _("To fill in the missing subjects, use the <strong>Edit basic information</strong> entry in the <strong>Actions</strong> menu for each image.")
            k_list.append(k_dict)
            for i in sqs.filter(
                (Q(subject_type = 100) | Q(subject_type = 200)) &
                (Q(subjects = None)) &
                (Q(solar_system_main_subject = None))):
                k_dict[l]['images'].append(i)

            l = _("No imaging telescopes or lenses, or no imaging cameras specified")
            k_dict = {l: {'message': None, 'images': []}}
            k_list.append(k_dict)
            k_dict[l]['message'] = _("To fill in the missing gear, use the <strong>Edit gear used</strong> entry in the <strong>Actions</strong> menu for each image.")
            for i in sqs.filter(
                Q(subject_type__lt = 500) &
                (Q(imaging_telescopes = None) | Q(imaging_cameras = None))):
                k_dict[l]['images'].append(i)

            l = _("No acquisition details specified")
            k_dict = {l: {'message': None, 'images': []}}
            k_list.append(k_dict)
            k_dict[l]['message'] = _("To fill in the missing acquisition details, use the <strong>Edit acquisition details</strong> entry in the <strong>Actions</strong> menu for each image.")
            for i in sqs.filter(
                Q(subject_type__lt = 500) &
                Q(acquisition = None)):
                k_dict[l]['images'].append(i)

            sqs = Image.objects.none()

        section = 'public'

    return object_list(
        request,
        queryset=sqs,
        template_name='user/profile.html',
        template_object_name='image',
        paginate_by = 20,
        extra_context = {'thumbnail_size':settings.THUMBNAIL_SIZE,
                         's3_url':settings.S3_URL,
                         'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
                         'user':user,
                         'profile':profile,
                         'follows':follows,
                         'private_message_form': PrivateMessageForm(),
                         'section':section,
                         'subsection':subsection,
                         'subtitle':subtitle,
                         'backlink':backlink,
                         'smart_albums':smart_albums,
                        })


@require_GET
def user_page_commercial_products(request, username):
    user = get_object_or_404(User, username = username)
    profile = get_object_or_404(UserProfile, user = user)

    response_dict = {
        'user': user,
        'profile': profile,
        'user_is_producer': user_is_producer(user),
        'user_is_retailer': user_is_retailer(user),
        'commercial_gear_list': CommercialGear.objects.filter(producer = user).exclude(gear = None),
        'retailed_gear_list': RetailedGear.objects.filter(retailer = user).exclude(gear = None),
        'claim_commercial_gear_form': ClaimCommercialGearForm(user = user),
        'merge_commercial_gear_form': MergeCommercialGearForm(user = user),
        'claim_retailed_gear_form': ClaimRetailedGearForm(user = user),
        'merge_retailed_gear_form': MergeRetailedGearForm(user = user),
    }

    return render_to_response(
        'user/profile/commercial/products.html',
        response_dict,
        context_instance = RequestContext(request)
    )


@require_GET
def user_page_favorites(request, username):
    user = get_object_or_404(User, username = username)

    return object_list(
        request,
        queryset = Image.objects.filter(favorite__user = user),
        template_name = 'user/favorites.html',
        template_object_name = 'image',
        paginate_by = 20,
        extra_context = {
            'thumbnail_size': settings.THUMBNAIL_SIZE,
            's3_url': settings.S3_URL,
            'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
            'user': user,
            'private_message_form': PrivateMessageForm(),
         }
     )


@require_GET
def user_page_card(request, username):
    """Shows the user's public page"""
    user = get_object_or_404(User, username = username)
    profile = UserProfile.objects.get(user=user)

    gear_list = [('Telescopes and lenses', profile.telescopes.all(), 'imaging_telescopes'),
                 ('Mounts'        , profile.mounts.all(), 'mounts'),
                 ('Cameras'       , profile.cameras.all(), 'imaging_cameras'),
                 ('Focal reducers', profile.focal_reducers.all(), 'focal_reducers'),
                 ('Software'      , profile.software.all(), 'software'),
                 ('Filters'       , profile.filters.all(), 'filters'),
                 ('Accessories'   , profile.accessories.all(), 'accessories'),
                ]

    # Calculate some stats
    from django.template.defaultfilters import timesince

    member_since = None
    date_time = user.date_joined.replace(tzinfo = None)
    diff = abs(date_time - datetime.datetime.today())
    span = timesince(date_time)
    span = span.split(",")[0] # just the most significant digit
    if span == "0 " + _("minutes"):
        member_since = _("seconds ago")
    else:
        member_since = _("%s ago") % span 

    last_login = user.last_login
    if request.user.is_authenticated():
        viewer_profile = UserProfile.objects.get(user = request.user)
        last_login = to_user_timezone(user.last_login, viewer_profile)

    sqs = SearchQuerySet()
    sqs = sqs.filter(username = user.username).models(Image)
    sqs = sqs.order_by('-uploaded')

    images = len(sqs)
    integrated_images = len(sqs.filter(integration__gt = 0))
    integration = sum([x.integration for x in sqs]) / 3600.0
    avg_integration = (integration / integrated_images) if integrated_images > 0 else 0
    stats = (
        (_('Member since'), member_since),
        (_('Last login'), last_login),
        (_('Images uploaded'), len(sqs)),
        (_('Total integration time'), "%.1f %s" % (integration, _("hours"))),
        (_('Average integration time'), "%.1f %s" % (avg_integration, _("hours"))),
    )

    return render_to_response(
        'user/card.html',
        {
            'user':user,
            'profile':profile,
            'gear_list':gear_list,
            'stats':stats,
        },
        context_instance = RequestContext(request))


@require_GET
def user_page_plots(request, username):
    """Shows the user's public page"""
    user = get_object_or_404(User, username = username)
    profile = UserProfile.objects.get(user=user)

    return render_to_response(
        'user/plots.html',
        {
            'user':user,
            'profile':profile,
        },
        context_instance = RequestContext(request))


@require_GET
def user_page_api_keys(request, username):
    """Shows the user's API Keys"""
    user = get_object_or_404(User, username = username)
    if user != request.user:
        return HttpResponseForbidden()

    profile = UserProfile.objects.get(user=user)
    keys = App.objects.filter(registrar = user)

    return render_to_response(
        'user/api_keys.html',
        {
            'user': user,
            'profile': profile,
            'api_keys': keys,
        },
        context_instance = RequestContext(request))


@require_GET
def user_profile_stats_get_integration_hours_ajax(request, username, period = 'monthly', since = 0):
    user = User.objects.get(username = username)

    import stats as _s
    (label, data, options) = _s.integration_hours(user, period, int(since))
    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def user_profile_stats_get_integration_hours_by_gear_ajax(request, username, period = 'monthly'):
    user = User.objects.get(username = username)

    import stats as _s
    (data, options) = _s.integration_hours_by_gear(user, period)
    response_dict = {
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def user_profile_stats_get_uploaded_images_ajax(request, username, period = 'monthly'):
    user = User.objects.get(username = username)

    import stats as _s
    (label, data, options) = _s.uploaded_images(user, period)
    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def user_profile_stats_get_views_ajax(request, username, period = 'daily'):
    user = User.objects.get(username = username)

    import stats as _s
    (label, data, options) = _s.views(user, period)
    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_get_image_views_ajax(request, id, period = 'daily'):
    import stats as _s

    (label, data, options) = _s.image_views(id, period)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@login_required
@require_GET
def user_profile_edit_basic(request):
    """Edits own profile"""
    profile = UserProfile.objects.get(user = request.user)
    form = UserProfileEditBasicForm(instance = profile)

    response_dict = {
        'form': form,
    }
    return render_to_response("user/profile/edit/basic.html",
        response_dict,
        context_instance=RequestContext(request))


@login_required
@require_POST
def user_profile_save_basic(request):
    """Saves the form"""

    profile = UserProfile.objects.get(user = request.user)
    form = UserProfileEditBasicForm(data=request.POST, instance = profile)
    response_dict = {'form': form}

    if not form.is_valid():
        return render_to_response("user/profile/edit/basic.html",
            response_dict,
            context_instance=RequestContext(request))

    form.save()

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect("/profile/edit/basic/");


@login_required
@user_passes_test(lambda u: user_is_producer(u) or user_is_retailer(u))
def user_profile_edit_commercial(request):
    profile = UserProfile.objects.get(user = request.user)
    if request.method == 'POST':
        form = UserProfileEditCommercialForm(data=request.POST, instance = profile)

        if form.is_valid():
            form.save()
            messages.success(request, _("Form saved. Thank you!"))
            return HttpResponseRedirect('/profile/edit/commercial/');
    else:
        form = UserProfileEditCommercialForm(instance = profile)

    return render_to_response("user/profile/edit/commercial.html",
        {
            'form': form,
        },
        context_instance=RequestContext(request))


@login_required
@user_passes_test(lambda u: user_is_retailer(u))
def user_profile_edit_retailer(request):
    profile = UserProfile.objects.get(user = request.user)
    if request.method == 'POST':
        form = UserProfileEditRetailerForm(data=request.POST, instance = profile)

        if form.is_valid():
            form.save()
            messages.success(request, _("Form saved. Thank you!"))
            return HttpResponseRedirect('/profile/edit/retailer/');
    else:
        form = UserProfileEditRetailerForm(instance = profile)

    return render_to_response("user/profile/edit/retailer.html",
        {
            'form': form,
        },
        context_instance=RequestContext(request))


@login_required
@require_GET
def user_profile_edit_license(request):
    profile = UserProfile.objects.get(user = request.user)
    form = DefaultImageLicenseForm(instance = profile)
    return render_to_response(
        'user/profile/edit/license.html',
        {'form': form},
        context_instance = RequestContext(request))


@login_required
@require_POST
def user_profile_save_license(request):
    profile = UserProfile.objects.get(user = request.user)
    form = DefaultImageLicenseForm(data = request.POST, instance = profile)

    if not form.is_valid():
        return render_to_response(
            'user/profile/edit/license.html',
            {'form': form},
            context_instance = RequestContext(request))

    form.save()

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect('/profile/edit/license/')


@login_required
@require_GET
def user_profile_edit_gear(request):
    """Edits own profile"""
    profile = UserProfile.objects.get(user=request.user)

    def uniq(seq):
       # Not order preserving
       keys = {}
       for e in seq:
           keys[e] = 1
       return keys.keys()

    response_dict = {
        'initial': 'initial' in request.GET,
        'all_gear_makes': simplejson.dumps(
            uniq([x.get_make() for x in Gear.objects.exclude(make = None).exclude(make = '')])),
        'all_gear_names': simplejson.dumps(
            uniq([x.get_name() for x in Gear.objects.exclude(name = None).exclude(name = '')])),
    }

    prefill = {}
    for attr, label, klass in (
        ['telescopes', _("Telescopes and lenses"), 'Telescope'],
        ['cameras', _("Cameras"), 'Camera'],
        ['mounts', _("Mounts"), 'Mount'],
        ['focal_reducers', _("Focal reducers"), 'FocalReducer'],
        ['software', _("Software"), 'Software'],
        ['filters', _("Filters"), 'Filter'],
        ['accessories', _("Accessories"), 'Accessory']):
        all_gear = getattr(profile, attr).all()
        prefill[label] = [all_gear, klass]

    response_dict['prefill'] = prefill
    return render_to_response("user/profile/edit/gear.html",
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_POST
def user_profile_edit_gear_remove(request, id):
    profile = UserProfile.objects.get(user = request.user)
    gear, gear_type = get_correct_gear(id)
    if not gear:
        raise Http404

    profile.remove_gear(gear, gear_type)

    return ajax_success()


@login_required
@require_GET
def user_profile_edit_locations(request):
    profile = UserProfile.objects.get(user = request.user)
    LocationsFormset = inlineformset_factory(
        UserProfile, Location, form = LocationEditForm, extra = 1)

    return render_to_response(
        'user/profile/edit/locations.html',
        {
            'formset': LocationsFormset(instance = profile),
            'profile': profile,
        },
        context_instance = RequestContext(request))


@login_required
@require_POST
def user_profile_save_locations(request):
    profile = UserProfile.objects.get(user = request.user)
    LocationsFormset = inlineformset_factory(
        UserProfile, Location, form = LocationEditForm, extra = 1)
    formset = LocationsFormset(data = request.POST, instance = profile)
    if not formset.is_valid():
        return render_to_response(
            'user/profile/edit/locations.html',
            {
                'formset': formset,
                'profile': profile,
            },
            context_instance = RequestContext(request))

    formset.save()
    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect('/profile/edit/locations/');


@login_required
@require_POST
def user_profile_save_gear(request):
    """Saves the form"""

    profile = UserProfile.objects.get(user = request.user)

    profile.telescopes.clear()
    profile.mounts.clear()
    profile.cameras.clear()
    profile.focal_reducers.clear()
    profile.filters.clear()
    profile.software.clear()
    profile.accessories.clear()

    form = UserProfileEditGearForm(data=request.POST)
    if not form.is_valid():
        response_dict = {"form": form}
        prefill_dict = {}
        for k in ("telescopes", "mounts", "cameras", "focal_reducers",
                  "software", "filters", "accessories",):
            allGear = getattr(profile, k).all()
            prefill_dict[k] = jsonDump(allGear)

        return render_to_response("user/profile/edit/gear.html",
            response_dict,
            context_instance=RequestContext(request))

    for k, v in {"telescopes"    : [Telescope, profile.telescopes],
                 "mounts"        : [Mount, profile.mounts],
                 "cameras"       : [Camera, profile.cameras],
                 "focal_reducers": [FocalReducer, profile.focal_reducers],
                 "software"      : [Software, profile.software],
                 "filters"       : [Filter, profile.filters],
                 "accessories"   : [Accessory, profile.accessories],
                }.iteritems():
        (names, value) = valueReader(request.POST, k)
        for name in names:
            try:
                id = float(name)
                gear_item = v[0].objects.get(id = id)
                automerge = GearAutoMerge.objects.filter(label = gear_item.get_name())
                if automerge:
                    gear_item = v[0].objects.get(gear_ptr__pk = automerge[0].master.pk)
            except ValueError:
                automerge = GearAutoMerge.objects.filter(label = name)
                if automerge:
                    gear_item = v[0].objects.get(gear_ptr__pk = automerge[0].master.pk)
                else:
                    gear_item, created = v[0].objects.get_or_create(name = name)
            except v[0].DoesNotExist:
                continue
            getattr(profile, k).add(gear_item)
        form.fields[k].initial = value

    profile.save()

    initial = "&initial=true" if "initial" in request.POST else ""
    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect("/profile/edit/gear/" + initial);


@login_required
def user_profile_flickr_import(request):
    response_dict = {}

    if 'flickr_token' in request.session:
        token = request.session['flickr_token']
    else:
        token = None
        if 'flickr_step' in request.session:
            del request.session['flickr_step']

    flickr = flickrapi.FlickrAPI(settings.FLICKR_API_KEY,
                                 settings.FLICKR_SECRET,
                                 token = token,
                                 store_token = False)
    if token:
        # We have a token, but it might not be valid
        try:
            flickr.auth_checkToken()
        except flickrapi.FlickrError:
            token = None
            del request.session['flickr_token']

    if not token:
        # We were never authenticated, or authentication expired. We need
        # to reauthenticate.
        link = flickr.web_login_url(perms='read')
        response_dict['flickr_link'] = link
        return render_to_response("user/profile/flickr_import.html",
            response_dict,
            context_instance=RequestContext(request))

    if not request.POST:
        # If we made it this far (it's a GET request), it means that we
        # are authenticated with flickr. Let's fetch the sets and send them to
        # the template.
        
        # Hole shit, does it have to be so insane to get the info on the
        # authenticated user?
        nsid = flickr.urls_getUserProfile().find('user').attrib['nsid']
        sets = flickr.photosets_getList().find('photosets').findall('photoset')
        template_sets = {}
        for set in sets:
            template_sets[set.find('title').text] = set.attrib['id']
        response_dict['flickr_sets'] = template_sets
    else:
        # This is POST!
        if 'id_flickr_set' in request.POST:
            set_id = request.POST['id_flickr_set']
            urls_sq = {}
            for photo in flickr.walk_set(set_id, extras='url_sq'):
                urls_sq[photo.attrib['id']] = photo.attrib['url_sq']
                response_dict['flickr_photos'] = urls_sq
        elif 'flickr_selected_photos[]' in request.POST:
            selected_photos = request.POST.getlist('flickr_selected_photos[]')
            # Starting the process of importing
            for index, photo_id in enumerate(selected_photos):
                sizes = flickr.photos_getSizes(photo_id = photo_id)
                info = flickr.photos_getInfo(photo_id = photo_id).find('photo')

                title = info.find('title').text
                description = info.find('description').text
 
                # Attempt to find the largest image
                found_size = None
                for label in ['Square', 'Thumbnail', 'Small', 'Medium', 'Medium640', 'Large', 'Original']:
                    for size in sizes.find('sizes').findall('size'):
                        if size.attrib['label'] == label:
                            found_size = size

                if found_size is not None:
                    source = found_size.attrib['source']
                    file = urllib2.urlopen(source)
                    filename = str(uuid4())
                    original_ext = '.jpg'
                    destination = open(settings.UPLOADS_DIRECTORY + filename + original_ext, 'wb+')
                    destination.write(file.read())
                    destination.close()

                    profile = UserProfile.objects.get(user = request.user)
                    image = Image(filename=filename, original_ext=original_ext,
                                  user=request.user,
                                  title=title if title is not None else '',
                                  description=description if description is not None else '',
                                  subject_type = 600, # Default to Other only when doing a Flickr import
                                  license = profile.default_license)
                    image.save()
                    image.process()

        return ajax_response(response_dict)

    return render_to_response("user/profile/flickr_import.html",
                              response_dict,
                              context_instance=RequestContext(request))


def flickr_auth_callback(request):
    f = flickrapi.FlickrAPI(settings.FLICKR_API_KEY,
                            settings.FLICKR_SECRET, store_token = False)

    if 'frob' in request.GET:
        frob = request.GET['frob']
        try:
            token = f.get_token(frob)
        except flickrapi.FlickrError:
            token = None
    else:
        token = None

    request.session['flickr_token'] = token

    return HttpResponseRedirect("/profile/edit/flickr/")


@login_required
@require_GET
def user_profile_edit_preferences(request):
    """Edits own preferences"""
    profile = UserProfile.objects.get(user=request.user)
    form = UserProfileEditPreferencesForm(instance=profile)
    response_dict = {
        'form': form,
    }
    email_medium = "1" # see NOTICE_MEDIA in notifications/models.py
    email_default = NOTICE_MEDIA_DEFAULTS[email_medium]
    notice_settings = NoticeSetting.objects.filter(
        user=request.user,
        medium=email_medium,
    )
    stored_settings = {}
    for setting in notice_settings:
        stored_settings[setting.notice_type.label] = setting.send

    for notice_type in NOTICE_TYPES:
        if notice_type[3] == 2:
            label = notice_type[0]
            value = stored_settings.get(label,
                                        notice_type[3] >= email_default)
            form.fields[label].initial = value

    return render_to_response("user/profile/edit/preferences.html",
        response_dict,
        context_instance=RequestContext(request))


@login_required
@require_POST
def user_profile_save_preferences(request):
    """Saves the form"""

    profile = UserProfile.objects.get(user=request.user)
    form = UserProfileEditPreferencesForm(data=request.POST, instance=profile)
    response_dict = {'form': form}

    if form.is_valid():
        form.save()
        # Activate the chosen language
        from django.utils.translation import check_for_language, activate
        lang = form.cleaned_data['language']
        if lang and check_for_language(lang):
            if hasattr(request, 'session'):
                request.session['django_language'] = lang
            activate(lang)

        # save the notification settings
        email_medium = "1" # see NOTICE_MEDIA in notifications/models.py
        for notice_type in NOTICE_TYPES:
            if notice_type[3] == 2:
                label = notice_type[0]
                import notification
                notice_object = notification.models.NoticeType.objects.get(label=label)
                value = form.cleaned_data[label]
                try:
                    setting = NoticeSetting.objects.get(
                        user=request.user,
                        notice_type=notice_object,
                        medium=email_medium
                    )
                    setting.send = value
                except NoticeSetting.DoesNotExist:
                    setting = NoticeSetting(
                        user=request.user,
                        notice_type=notice_object,
                        medium=email_medium,
                        send=value
                    )
                setting.save()
    else:
        return render_to_response("user/profile/edit/preferences.html",
            response_dict,
            context_instance=RequestContext(request))

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect("/profile/edit/preferences/");


@login_required
@require_GET
def follow(request, username):
    from_profile = UserProfile.objects.get(user=request.user)
    to_user = get_object_or_404(User, username=username)
    to_profile = get_object_or_404(UserProfile, user=to_user)

    if to_profile not in from_profile.follows.all():
        from_profile.follows.add(to_profile)

    push_notification([to_user], 'new_follower',
                      {'object':request.user.username,
                       'object_url':from_profile.get_absolute_url()})
    push_notification([request.user], 'follow_success',
                      {'object':username,
                       'object_url':to_profile.get_absolute_url()})

    if request.is_ajax():
        return ajax_success()
    else:
        next_page = '/'
        if 'next' in request.GET:
            next_page = request.GET.get('next')
        return HttpResponseRedirect(next_page)


@login_required
@require_GET
def unfollow(request, username):
    from_profile = UserProfile.objects.get(user=request.user)
    to_user = get_object_or_404(User, username=username)
    to_profile = get_object_or_404(UserProfile, user=to_user)

    if to_profile in from_profile.follows.all():
        from_profile.follows.remove(to_profile)

    push_notification([request.user], 'unfollow_success',
                      {'object':username,
                       'object_url':to_profile.get_absolute_url()})

    if request.is_ajax():
        return ajax_success()
    else:
        next_page = '/'
        if 'next' in request.GET:
            next_page = request.GET.get('next')
        return HttpResponseRedirect(next_page)


@login_required
@require_GET
def follow_gear(request, id):
    gear = get_object_or_404(Gear, id = id)
    profile = UserProfile.objects.get(user = request.user)

    if gear not in profile.follows_gear.all():
        profile.follows_gear.add(gear)
        profile.save()
        if request.is_ajax():
            return ajax_success()
        else:
            next_page = '/'
            if 'next' in request.GET:
                next_page = request.GET.get('next')
            return HttpResponseRedirect(next_page)

    return ajax_fail()


@login_required
@require_GET
def unfollow_gear(request, id):
    gear = get_object_or_404(Gear, id = id)
    profile = UserProfile.objects.get(user = request.user)

    if gear in profile.follows_gear.all():
        profile.follows_gear.remove(gear)
        profile.save()
        if request.is_ajax():
            return ajax_success()
        else:
            next_page = '/'
            if 'next' in request.GET:
                next_page = request.GET.get('next')
            return HttpResponseRedirect(next_page)

    return ajax_fail()


@login_required
@require_GET
def follow_subject(request, id):
    subject = get_object_or_404(Subject, id = id)
    profile = UserProfile.objects.get(user = request.user)

    if subject not in profile.follows_subjects.all():
        profile.follows_subjects.add(subject)
        profile.save()
        if request.is_ajax():
            return ajax_success()
        else:
            next_page = '/'
            if 'next' in request.GET:
                next_page = request.GET.get('next')
            return HttpResponseRedirect(next_page)

    return ajax_fail()


@login_required
@require_GET
def unfollow_subject(request, id):
    subject = get_object_or_404(Subject, id = id)
    profile = UserProfile.objects.get(user = request.user)

    if subject in profile.follows_subjects.all():
        profile.follows_subjects.remove(subject)
        profile.save()
        if request.is_ajax():
            return ajax_success()
        else:
            next_page = '/'
            if 'next' in request.GET:
                next_page = request.GET.get('next')
            return HttpResponseRedirect(next_page)

    return ajax_fail()


@login_required
@require_GET
def mark_notifications_seen(request):
    for n in notification.Notice.objects.filter(user=request.user):
        n.is_unseen()
    return ajax_success()


@login_required
@require_GET
def notifications(request):
    for n in notification.Notice.objects.filter(user=request.user):
        n.is_unseen()

    return object_list(
        request, 
        queryset=notification.Notice.objects.filter(user=request.user),
        template_name='notification/all.html',
        template_object_name='notification')


@login_required
@require_POST
def send_private_message(request):
    form = PrivateMessageForm(data=request.POST)
    if form.is_valid():
        subject = form.cleaned_data['subject']
        body    = form.cleaned_data['body']
        to_user = request.POST['to_user']

        recipient = User.objects.get(username=to_user)
        message = persistent_messages.add_message(
            request, persistent_messages.SUCCESS, body,
            subject=subject, user=recipient, from_user=request.user)
        push_message(recipient, {'sender':request.user.username,
                                 'subject': subject,
                                 'message_id': message.id if message is not None else 0})
        try:
            reqs = ImageRequest.objects.filter(
                to_user = request.user,
                from_user = recipient,
                type = "FITS",
                fulfilled = False)
            for req in reqs:
                req.fulfilled = True
                req.save()
        except:
            pass

        return ajax_success()
    return ajax_fail()


@login_required
@require_GET
def bring_to_attention(request, id):
    image = get_object_or_404(Image, id=id)
    form = BringToAttentionForm()

    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'form': form,
        'image': image,
    }
    return render_to_response(
        'image/actions/bring_to_attention.html',
        response_dict,
        context_instance = RequestContext(request))

  
@login_required
@require_POST
def bring_to_attention_process(request):
    form = BringToAttentionForm(data=request.POST)
    image_id = request.POST.get('image_id')
    image = get_object_or_404(Image, id=image_id)

    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'form': form,
        'image': image,
    }
    if not form.is_valid():
        return render_to_reponse(
            'image/actions/bring_to_attention.html',
            response_dict,
            context_instance = RequestContext(request))

    (usernames, value) = valueReader(request.POST, 'users')
    recipients = []
    for username in usernames:
        user = User.objects.get(username=username)
        if user is not None:
            recipients.append(user)

    push_notification(recipients, 'attention_request',
                      {'object':image,
                       'object_url':settings.ASTROBIN_BASE_URL + image.get_absolute_url(),
                       'originator':request.user,
                       'originator_url': request.user.get_absolute_url()})

    return HttpResponseRedirect('/%d/bring-to-attention/complete/' % image.id)


@login_required
@require_GET
def bring_to_attention_complete(request, id):
    image = get_object_or_404(Image, id=id)

    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'image': image,
    }
    return render_to_response(
        'image/actions/bring_to_attention_complete.html',
        response_dict,
        context_instance = RequestContext(request))


@login_required
@require_GET
def requests(request):
    return object_list(
        request,
        queryset=Request.objects.filter(to_user=request.user).select_subclasses(),
        template_name='requests/all.html',
        template_object_name='req',
        extra_context={})


@login_required
@require_GET
def image_request_additional_information(request, image_id):
    image = get_object_or_404(Image, id=image_id)

    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'image': image,
    }
    return render_to_response(
        'image/actions/request_additional_information.html',
        response_dict,
        context_instance = RequestContext(request))


@login_required
@require_GET
def image_request_additional_information_process(request, image_id):
    image = get_object_or_404(Image, id=image_id)

    message = _('<strong>%s</strong> has requested additional information about your image.') % request.user
    r = ImageRequest(
        from_user=request.user,
        to_user=image.user,
        image=image,
        fulfilled=False,
        message=message, # not implemented yet
        type='INFO')
    r.save()
    push_request(image.user, r)

    return HttpResponseRedirect('/request/image/additional-information/complete/%s/' % image.id)


@login_required
@require_GET
def image_request_additional_information_complete(request, image_id):
    image = get_object_or_404(Image, id=image_id)

    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'image': image,
    }
    return render_to_response(
        'image/actions/request_additional_information_complete.html',
        response_dict,
        context_instance = RequestContext(request))


@login_required
@require_GET
def image_request_fits(request, image_id):
    image = get_object_or_404(Image, id=image_id)

    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'image': image,
    }
    return render_to_response(
        'image/actions/request_fits.html',
        response_dict,
        context_instance = RequestContext(request))


@login_required
@require_GET
def image_request_fits_process(request, image_id):
    image = get_object_or_404(Image, id=image_id)

    # message not implemented yet, let's hard code it for the notification
    message = _('<strong>%s</strong> has requested to see the TIFF or FITS of your image.') % request.user
    r = ImageRequest(
        from_user=request.user,
        to_user=image.user,
        image=image,
        fulfilled=False,
        message=message, # not implemented yet
        type='FITS')
    r.save()
    push_request(image.user, r)

    return HttpResponseRedirect('/request/image/fits/complete/%s/' % image.id)


@login_required
@require_GET
def image_request_fits_complete(request, image_id):
    image = get_object_or_404(Image, id=image_id)

    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        'image': image,
    }
    return render_to_response(
        'image/actions/request_fits_complete.html',
        response_dict,
        context_instance = RequestContext(request))


@login_required
@require_GET
def request_mark_fulfilled(request, request_id):
    req = get_object_or_404(Request, id=request_id)
    if req.to_user != request.user:
        return HttpResponseForbidden()

    req.fulfilled = True
    req.save()

    return HttpResponseRedirect('/requests/')


@login_required
@require_POST
def image_revision_upload_process(request):
    def upload_error(image):
        messages.error(request, _("Invalid image or no image provided. Allowed formats are JPG, PNG and GIF."))
        return HttpResponseRedirect(image.get_absolute_url())

    file = None
    image_id = request.POST['image_id']
    image = Image.objects.get(id=image_id)

    form = ImageRevisionUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return upload_error(image)
    file = request.FILES["file"]

    filename, original_ext = str(uuid4()), os.path.splitext(file.name)[1]
    original_ext = original_ext.lower()
    if original_ext == '.jpeg':
        original_ext = '.jpg'
    if original_ext not in ('.jpg', '.png', '.gif'):
        return upload_error(image)

    try:
        from PIL import Image as PILImage
        trial_image = PILImage.open(file)
        trial_image.verify()
    except:
        return upload_error(image)

    destination = open(settings.UPLOADS_DIRECTORY + filename + original_ext, 'wb+')
    for chunk in file.chunks():
        destination.write(chunk)
    destination.close()

    revisions = ImageRevision.objects.filter(image = image).order_by('id')
    highest_label = 'A'
    for r in revisions:
        r.is_final = False
        r.save()
        highest_label = r.label

    image.is_final = False
    image.save()

    image_revision = ImageRevision(
        image = image,
        filename = filename,
        original_ext = original_ext,
        is_final = True,
        label = base26_encode(ord(highest_label) - ord('A') + 1),
    )
    image_revision.save()
    image_revision.process()

    return HttpResponseRedirect(image_revision.get_absolute_url())


@require_GET
def stats(request):
    response_dict = {}

    sqs = SearchQuerySet()
    gs = GlobalStat.objects.all()[0]

    response_dict['total_users'] = gs.users
    response_dict['total_images'] = gs.images
    response_dict['total_integration'] = gs.integration

    sort = '-user_integration'
    if 'sort' in request.GET:
        sort = request.GET.get('sort')
        if sort == 'tot_integration':
            sort = '-user_integration'
        elif sort == 'avg_integration':
            sort = '-user_avg_integration'
        elif sort == 'images':
            sort = '-user_images'

    queryset = sqs.filter(user_images__gt = 0).models(User).order_by(sort)

    return object_list(
        request,
        queryset = queryset,
        template_name = 'stats.html',
        template_object_name = 'user',
        extra_context = response_dict,
    )


@require_GET
def leaderboard(request):
    response_dict = {}

    sqs = SearchQuerySet()
    sort = '-user_integration'
    if 'sort' in request.GET:
        sort = request.GET.get('sort')
        if sort == 'tot_integration':
            sort = '-integration'
        elif sort == 'avg_integration':
            sort = '-avg_integration'
        elif sort == 'images':
            sort = '-images'
        elif sort == 'comments':
            sort = '-comments_written'

    queryset = sqs.models(User).order_by(sort)

    return object_list(
        request,
        queryset = queryset,
        template_name = 'leaderboard.html',
        template_object_name = 'user',
        extra_context = response_dict,
    )


@require_GET
def help(request):
    return render_to_response('help.html',
        context_instance=RequestContext(request))


@require_GET
def api(request):
    return render_to_response('api.html',
        {
            's3_url': settings.S3_URL,
            'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        },
        context_instance=RequestContext(request))


@require_GET
def affiliates(request):
    return object_list(
        request,
        queryset = UserProfile.objects
            .filter(
                Q(user__groups__name = 'Producers') |
                Q(user__groups__name = 'Retailers'))
            .exclude(
                Q(company_name = None) |
                Q(company_name = "")).distinct(),
        template_name = 'affiliates.html',
        template_object_name = 'affiliate',
        paginate_by = 100,
    )


@require_GET
def faq(request):
    return render_to_response('faq.html',
        context_instance=RequestContext(request))


@require_GET
def tos(request):
    return render_to_response('tos.html',
        context_instance=RequestContext(request))

@require_GET
def guidelines(request):
    return render_to_response('guidelines.html',
        context_instance=RequestContext(request))


@login_required
@require_GET
def location_edit(request, id):
    location = get_object_or_404(Location, pk=id)
    form = LocationEditForm(instance=location)

    return render_to_response('location/edit.html',
        {'form': form,
         'id'  : id,
        },
        context_instance=RequestContext(request))


@require_GET
def set_language(request, lang):
    from django.utils.translation import check_for_language, activate

    next = request.REQUEST.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', None)
    if not next:
        next = '/'
    response = HttpResponseRedirect(next)
    if lang and check_for_language(lang):
        if hasattr(request, 'session'):
            request.session['django_language'] = lang

        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
        activate(lang)

    if request.user.is_authenticated():
        profile = UserProfile.objects.get(user = request.user)
        profile.language = lang
        profile.save()

    return response


@require_GET
def nightly(request):
    month_offset = int(request.GET.get('month_offset', 0))
    start = monthdelta(datetime.datetime.today().date(), -month_offset)
    sqs = None
    daily = []
    total = 0

    for date in (start - datetime.timedelta(days = x) for x in range(1, start.day)):
        k_dict = {date: []}
        daily.append(k_dict)
        for i in Image.objects.filter(acquisition__date = date, is_wip = False, is_stored = True).distinct():
            k_dict[date].append(i)
            total += 1

    return object_list(
        request,
        queryset = Image.objects.none(), # Cheating at object_list
        paginate_by = 1,
        template_name = 'nightly.html',
        extra_context = {
            'thumbnail_size': settings.THUMBNAIL_SIZE,
            's3_url': settings.S3_URL,
            'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
            'daily': daily,
            'total': total,
            'month_offset': month_offset,
            'previous_month': month_offset - 1,
            'next_month': month_offset + 1,
            'current_month_label': start,
            'previous_month_label': monthdelta(start, 1),
            'next_month_label': monthdelta(start, -1)
        })


@require_POST
@login_required
def image_comment_save(request):
    form = CommentForm(data = request.POST)

    if form.is_valid():
        author = User.objects.get(id = form.data['author'])
        image = Image.objects.get(id = form.data['image'])
        if request.user != author:
            return HttpResponseForbidden()

        comment = form.save(commit = False)
        comment.author = author
        comment.image = image
        if form.data['parent_id'] != '':
            comment.parent = Comment.objects.get(id = form.data['parent_id'])

        comment.save()

        notification = 'new_comment'
        recipient = image.user
        url = '%s/%d#c%d' % (settings.ASTROBIN_BASE_URL, image.id, comment.id)
        if comment.parent:
            notification = 'new_comment_reply'
            recipient = comment.parent.author

        if recipient != author:
            push_notification(
                [recipient], notification,
                {
                    'url': url,
                    'user': author,
                }
            )
                
        response_dict = {
            'success': True,
            'comment_id': comment.id,
            'comment': comment.comment,
            'action': 'save',
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype = 'application/javascript')

    return ajax_fail()


@require_GET
@login_required
def image_comment_delete(request, id):
    comment = get_object_or_404(Comment, id = id)
    if comment.author != request.user:
        return HttpResponseForbidden()

    # NOTE: this function undeletes too!
    comment.is_deleted = not comment.is_deleted
    comment.save()

    response_dict = {
        'success': True,
        'deleted': comment.is_deleted,
        'comment': comment.comment,
    }
    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_GET
@login_required
def image_comment_get(request, id):
    comment = get_object_or_404(Comment, id = id)

    response_dict = {
        'success': True,
        'comment': comment.comment,
    }
    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_POST
@login_required
def image_comment_edit(request):
    form = CommentForm(data = request.POST)

    if form.is_valid():
        author = User.objects.get(id = form.data['author'])
        image = Image.objects.get(id = form.data['image'])
        if request.user != author:
            return HttpResponseForbidden()

        comment = Comment.objects.get(id = form.data['parent_id'])
        comment.comment = form.cleaned_data['comment']
        comment.save()

        response_dict = {
            'success': True,
            'comment_id': comment.id,
            'comment': comment.comment,
            'action': 'edit',
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype = 'application/javascript')

    return ajax_fail()


@require_GET
@login_required
@never_cache
def get_edit_gear_form(request, id):
    gear, gear_type = get_correct_gear(id)
    if not gear:
        raise Http404

    form = None
    if gear_type == 'Telescope':
        form = TelescopeEditForm(instance = gear)
    elif gear_type == 'Mount':
        form = MountEditForm(instance = gear)
    elif gear_type == 'Camera':
        form = CameraEditForm(instance = gear)
    elif gear_type == 'FocalReducer':
        form = FocalReducerEditForm(instance = gear)
    elif gear_type == 'Software':
        form = SoftwareEditForm(instance = gear)
    elif gear_type == 'Filter':
        form = FilterEditForm(instance = gear)
    elif gear_type == 'Accessory':
        form = AccessoryEditForm(instance = gear)

    from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
    response_dict = {
        'form': as_bootstrap(form, 'horizontal') if form else '',
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_GET
@login_required
def get_empty_edit_gear_form(request, gear_type):
    form_lookup = {
        'Telescope': TelescopeEditNewForm,
        'Mount': MountEditNewForm,
        'Camera': CameraEditNewForm,
        'FocalReducer': FocalReducerEditNewForm,
        'Software': SoftwareEditNewForm,
        'Filter': FilterEditNewForm,
        'Accessory': AccessoryEditNewForm,
    }

    form = form_lookup[gear_type]()
    from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
    response_dict = {
        'form': as_bootstrap(form, 'horizontal') if form else '',
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_POST
@login_required
def save_gear_details(request):
    gear = None
    if 'gear_id' in request.POST:
        id = request.POST.get('gear_id')
        gear, gear_type = get_correct_gear(id)
    else:
        gear_type = request.POST.get('gear_type')

    from gear import CLASS_LOOKUP

    form_lookup = {
        'Telescope': TelescopeEditNewForm,
        'Mount': MountEditNewForm,
        'Camera': CameraEditNewForm,
        'FocalReducer': FocalReducerEditNewForm,
        'Software': SoftwareEditNewForm,
        'Filter': FilterEditNewForm,
        'Accessory': AccessoryEditNewForm,
    }

    if gear and gear.get_name() != '':
        form_lookup = {
            'Telescope': TelescopeEditForm,
            'Mount': MountEditForm,
            'Camera': CameraEditForm,
            'FocalReducer': FocalReducerEditForm,
            'Software': SoftwareEditForm,
            'Filter': FilterEditForm,
            'Accessory': AccessoryEditForm,
        }

    user_gear_lookup = {
        'Telescope': 'telescopes',
        'Mount': 'mounts',
        'Camera': 'cameras',
        'FocalReducer': 'focal_reducers',
        'Software': 'software',
        'Filter': 'filters',
        'Accessory': 'accessories',
    }

    created = False
    name = request.POST.get('name')
    filters = Q(name = name)
    if request.POST.get('make'):
        filters = filters & Q(make = request.POST.get('make'))

    if not gear:
        try:
            if request.POST.get('make'):
                gear, created = CLASS_LOOKUP[gear_type].objects.get_or_create(
                    make = request.POST.get('make'),
                    name = request.POST.get('name'))
            else:
                gear, created = CLASS_LOOKUP[gear_type].objects.get_or_create(
                    name = request.POST.get('name'))
        except CLASS_LOOKUP[gear_type].MultipleObjectsReturned:
            gear = CLASS_LOOKUP[gear_type].objects.filter(filters)[0]
            created = False

    form = form_lookup[gear_type](data = request.POST, instance = gear)
    if not form.is_valid():
        from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
        response_dict = {
            'form': as_bootstrap(form, 'horizontal') if form else '',
            'gear_id': gear.id,
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype = 'application/javascript')

    form.save()

    profile = UserProfile.objects.get(user = request.user)
    user_gear = getattr(profile, user_gear_lookup[gear_type])
    if gear not in user_gear.all():
        user_gear.add(gear)

    alias = _("no alias")
    gear_user_info = GearUserInfo(gear = gear, user = request.user)
    if gear_user_info.alias is not None and gear_user_info.alias != '':
        alias = gear_user_info.alias

    response_dict = {
        'success': True,
        'id': gear.id,
        'make': gear.get_make(),
        'name': gear.get_name(),
        'alias': alias,
        'complete': is_gear_complete(gear.id),
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_GET
@login_required
@never_cache
def get_is_gear_complete(request, id):
    return HttpResponse(
        simplejson.dumps({'complete': is_gear_complete(id)}),
        mimetype = 'application/javascript')


@require_GET
@login_required
@never_cache
def get_gear_user_info_form(request, id):
    gear = get_object_or_404(Gear, id = id)
    gear_user_info, created = GearUserInfo.objects.get_or_create(
        gear = gear,
        user = request.user,
    )

    form = GearUserInfoForm(instance = gear_user_info)

    from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
    response_dict = {
        'form': as_bootstrap(form, 'horizontal') if form else '',
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_POST
@login_required
def save_gear_user_info(request):
    gear = get_object_or_404(Gear, id = request.POST.get('gear_id'))
    gear_user_info, created = GearUserInfo.objects.get_or_create(
        gear = gear,
        user = request.user,
    )

    form = GearUserInfoForm(data = request.POST, instance = gear_user_info)
    if not form.is_valid():
        from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
        response_dict = {
            'form': as_bootstrap(form, 'horizontal') if form else '',
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype = 'application/javascript')

    form.save()
    return ajax_success()


@require_GET
@login_required
@never_cache
def favorite_ajax(request, id):
    image = get_object_or_404(Image, pk=id)

    f, created = Favorite.objects.get_or_create(image = image, user = request.user)
    if not created:
        f.delete()
    else:
        f.save()

    if image.user != request.user and created:
        push_notification(
            [image.user], 'new_favorite',
            {
                'url': settings.ASTROBIN_BASE_URL + image.get_absolute_url(),
                'user': request.user,
            }
        )

    return HttpResponse(
        simplejson.dumps({
            'created': created,
            'favorites': Favorite.objects.filter(image = image).count(),
        }),
        mimetype = 'application/javascript')


@require_GET
@never_cache
def gear_popover_ajax(request, id):
    gear, gear_type = get_correct_gear(id)
    profile = UserProfile.objects.get(user = request.user) \
              if request.user.is_authenticated() \
              else None
    template = 'popover/gear.html'

    if gear_type == 'Telescope':
        template = 'popover/gear_telescope.html'
    elif gear_type == 'Mount':
        template = 'popover/gear_mount.html'
    elif gear_type == 'Camera':
        template = 'popover/gear_camera.html'
    elif gear_type == 'FocalReducer':
        template = 'popover/gear_focal_reducer.html'
    elif gear_type == 'Software':
        template = 'popover/gear_software.html'
    elif gear_type == 'Filter':
        template = 'popover/gear_filter.html'
    elif gear_type == 'Accessory':
        template = 'popover/gear_accessory.html'

    follows = Gear.objects.get(id = gear.id) in profile.follows_gear.all() \
              if profile \
              else False
    html = render_to_string(template,
        {
            'user': request.user,
            'gear': gear,
            'follows': follows,
            'is_authenticated': request.user.is_authenticated(),
            's3_url': settings.S3_URL,
            'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        })

    response_dict = {
        'success': True,
        'html': html,
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_GET
@never_cache
def subject_popover_ajax(request, id):
    subject = get_object_or_404(Subject, id = id)
    template = 'popover/subject.html'
    profile = UserProfile.objects.get(user = request.user) \
              if request.user.is_authenticated() \
              else None

    follows = subject in profile.follows_subjects.all() \
              if profile \
              else False

    html = render_to_string(template,
        {
            'subject': subject,
            'follows': follows,
            'is_authenticated': request.user.is_authenticated(),
        })

    response_dict = {
        'success': True,
        'html': html,
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_GET
@never_cache
def user_popover_ajax(request, username):
    user = get_object_or_404(User, username = username)
    template = 'popover/user.html'
    profile = UserProfile.objects.get(user = request.user) \
              if request.user.is_authenticated() \
              else None

    follows = user in profile.follows.all() \
              if profile \
              else False

    from django.template.defaultfilters import timesince

    member_since = None
    date_time = user.date_joined.replace(tzinfo = None)
    diff = abs(date_time - datetime.datetime.today())
    span = timesince(date_time)
    span = span.split(",")[0] # just the most significant digit
    if span == "0 " + _("minutes"):
        member_since = _("seconds ago")
    else:
        member_since = _("%s ago") % span 

    html = render_to_string(template,
        {
            'user': user,
            'images': Image.objects.filter(user = user).count(),
            'member_since': member_since,
            'follows': follows,
            'is_authenticated': request.user.is_authenticated(),
        })

    response_dict = {
        'success': True,
        'html': html,
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_GET
def subject_page(request, id):
    subject = get_object_or_404(Subject, id = id)

    all_images = Image.objects.filter(subjects = subject)

    integration_list = DeepSky_Acquisition.objects \
        .filter(image__subjects = subject) \
        .exclude(Q(number = None) | Q(duration = None)) \
        .values_list('number', 'duration')

    total_integration = '0'
    if integration_list:
        total_integration = '%.2f' % \
            (reduce(lambda x, y: x+y,
                    [x[0]*x[1] for x in integration_list]) \
            / 3600.00)

    return object_detail(
        request,
        queryset = Subject.objects.all(),
        object_id = id,
        template_name = 'subject/page.html',
        template_object_name = 'subject',
        extra_context = {
            'examples': all_images.order_by('-rating_score')[:10],
            'total_images': all_images.count(),
            'total_integration': total_integration,
        })


@require_GET
def gear_page(request, id, slug):
    gear, gear_type = get_correct_gear(id)
    if not gear:
        try:
            redirect = GearHardMergeRedirect.objects.get(fro = id)
        except GearHardMergeRedirect.DoesNotExist:
            raise Http404

        gear, gear_type = get_correct_gear(redirect.to)
        if not gear:
            raise Http404
        else:
            return HttpResponseRedirect(gear.get_absolute_url())

    image_attr_lookup = {
        'Telescope': 'imaging_telescopes',
        'Camera': 'imaging_cameras',
        'Mount': 'mounts',
        'FocalReducer': 'focal_reducers',
        'Software': 'software',
        'Filter': 'filters',
        'Accessory': 'accessories',
    }

    user_attr_lookup = {
        'Telescope': 'telescopes',
        'Camera': 'cameras',
        'Mount': 'mounts',
        'FocalReducer': 'focal_reducers',
        'Software': 'software',
        'Filter': 'filters',
        'Accessory': 'accessories',
    }

    from gear import CLASS_LOOKUP

    all_images = Image.objects.filter(**{image_attr_lookup[gear_type]: gear})
    commercial_image_revisions = None
    if gear.commercial and gear.commercial.image:
        commercial_image_revisions = ImageRevision.objects.filter(image = gear.commercial.image)

    from django.contrib.contenttypes.models import ContentType
    return object_detail(
        request,
        queryset = Gear.objects.all(),
        object_id = id,
        template_name = 'gear/page.html',
        template_object_name = 'gear',
        extra_context = {
            's3_url': settings.S3_URL,
            'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
            'examples': all_images.order_by('-rating_score')[:30],
            'small_size': settings.SMALL_THUMBNAIL_SIZE,
            'review_form': ReviewedItemForm(instance = ReviewedItem(content_type = ContentType.objects.get_for_model(Gear), content_object = gear)),
            'reviews': ReviewedItem.objects.filter(gear = gear),
            'comment_form': CommentForm(),
            'comments': GearComment.objects.filter(gear = gear),
            'owners_count': UserProfile.objects.filter(**{user_attr_lookup[gear_type]: gear}).count(),
            'images_count': Image.by_gear(gear).count(),
            'attributes': [
                (_(CLASS_LOOKUP[gear_type]._meta.get_field(k[0]).verbose_name),
                 getattr(gear, k[0]),
                 k[1]) for k in gear.attributes()],
            'commercial_image_revisions': commercial_image_revisions,
        })


@require_GET
def stats_subject_images_monthly_ajax(request, id):
    import stats as _s

    (label, data, options) = _s.subject_images_monthly(id)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_subject_integration_monthly_ajax(request, id):
    import stats as _s

    (label, data, options) = _s.subject_integration_monthly(id)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_subject_total_images_ajax(request, id):
    import stats as _s

    (label, data, options) = _s.subject_total_images(id)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_subject_camera_types_ajax(request, id):
    import stats as _s

    (label, data, options) = _s.subject_camera_types(id, request.LANGUAGE_CODE)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_subject_telescope_types_ajax(request, id):
    import stats as _s

    (label, data, options) = _s.subject_telescope_types(id, request.LANGUAGE_CODE)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_camera_types_trend_ajax(request):
    import stats as _s

    (data, options) = _s.camera_types_trend()

    response_dict = {
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_telescope_types_trend_ajax(request):
    import stats as _s

    (data, options) = _s.telescope_types_trend()

    response_dict = {
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_subject_type_trend_ajax(request):
    import stats as _s

    (data, options) = _s.subject_type_trend()

    response_dict = {
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_gear_total_images_ajax(request, id):
    import stats as _s

    (label, data, options) = _s.gear_total_images(id)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def gear_by_image(request, image_id):
    image = get_object_or_404(Image, id = image_id)

    attrs = ('imaging_telescopes', 'guiding_telescopes', 'mounts',
             'imaging_cameras', 'guiding_cameras', 'focal_reducers',
             'software', 'filters', 'accessories',)
    response_dict = {}

    for attr in attrs:
        ids = [int(x) for x in getattr(image, attr).all().values_list('id', flat = True)]
        response_dict[attr] = ids

    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_GET
def gear_by_make(request, make):
    klass = request.GET.get('klass', Gear)
    unclaimed = request.GET.get('unclaimed', False)

    ret = {
        'make': make,
        'gear': []
    }

    from gear import CLASS_LOOKUP

    try:
        autorename = GearMakeAutoRename.objects.get(rename_from = make)
        ret['make'] = autorename.rename_to
    except:
        pass

    if klass != Gear:
        klass = CLASS_LOOKUP[klass]

    gear = klass.objects.filter(make = ret['make']).order_by('name')

    if unclaimed == 'true':
        gear = gear.filter(commercial = None)

    ret['gear'] = [{'id': x.id, 'name': x.get_name()} for x in gear]

    return HttpResponse(
        simplejson.dumps(ret),
        mimetype = 'application/javascript')


@require_GET
def gear_by_ids(request, ids):
    filters = reduce(operator.or_, [Q(**{'id': x}) for x in ids.split(',')])
    gear = [[str(x.id), x.get_make(), x.get_name()] for x in Gear.objects.filter(filters)]
    return HttpResponse(
        simplejson.dumps(gear),
        mimetype = 'application/javascript')


@require_GET
def get_makes_by_type(request, klass):
    ret = {
        'makes': []
    }

    from gear import CLASS_LOOKUP
    from utils import unique_items

    ret['makes'] = unique_items([x.get_make() for x in CLASS_LOOKUP[klass].objects.exclude(make = '').exclude(make = None)])
    return HttpResponse(
        simplejson.dumps(ret),
        mimetype = 'application/javascript')


@require_GET
@login_required
def app_api_key_request(request):
    form = AppApiKeyRequestForm()

    return render_to_response(
        'app_api_key_request.html',
        {
            'form': form,
        },
        context_instance = RequestContext(request))


@require_POST
@login_required
def app_api_key_request_process(request):
    key_request = AppApiKeyRequest(registrar = request.user)
    form = AppApiKeyRequestForm(data = request.POST, instance = key_request)
    if not form.is_valid():
        return render_to_response(
            'app_api_key_request.html',
            {
                'form': form,
            },
            context_instance = RequestContext(request))

    form.save()
    return HttpResponseRedirect('/api/request-key/complete/');


@require_GET
@login_required
def app_api_key_request_complete(request):
    return render_to_response(
        'app_api_key_request_complete.html',
        {},
        context_instance = RequestContext(request))


@require_GET
@login_required
def gear_fix(request, id):
    # Disable this view for now. We're good.
    return HttpResponseForbidden()

    gear = get_object_or_404(Gear, id = id)
    form = ModeratorGearFixForm(instance = gear)
    next_gear = Gear.objects.filter(moderator_fixed = None).order_by('?')[:1].get()

    return render_to_response(
        'gear/fix.html',
        {
            'form': form,
            'gear': gear,
            'next_gear': next_gear,
            'already_fixed': Gear.objects.exclude(moderator_fixed = None).count(),
            'remaining': Gear.objects.filter(moderator_fixed = None).count(),
        },
        context_instance = RequestContext(request))


@require_POST
@login_required
def gear_fix_save(request):
    # Disable this view for now. We're good.
    return HttpResponseForbidden()

    id = request.POST.get('gear_id')
    gear = get_object_or_404(Gear, id = id)
    form = ModeratorGearFixForm(data = request.POST, instance = gear)
    next_gear = Gear.objects.filter(moderator_fixed = None).order_by('?')[:1].get()

    if not form.is_valid():
        return render_to_response(
            'gear/fix.html',
            {
                'form': form,
                'gear': gear,
                'next_gear': next_gear,
                'already_fixed': Gear.objects.exclude(moderator_fixed = None).count(),
                'remaining': Gear.objects.filter(moderator_fixed = None).count(),
            },
            context_instance = RequestContext(request))

    form.save()
    return HttpResponseRedirect('/gear/fix/%d/' % next_gear.id)


@require_GET
@login_required
def gear_fix_thanks(request):
    # Disable this view for now. We're good.
    return HttpResponseForbidden()

    return render_to_response(
        'gear/fix_thanks.html',
        context_instance = RequestContext(request))


@require_POST
@login_required
def gear_review_save(request):
    form = ReviewedItemForm(data = request.POST)

    if form.is_valid():
        gear, gear_type = get_correct_gear(form.data['gear_id'])
        review = form.save(commit = False)
        review.content_object = gear
        review.user = request.user
        review.save()

        user_attr_lookup = {
            'Telescope': 'telescopes',
            'Camera': 'cameras',
            'Mount': 'mounts',
            'FocalReducer': 'focal_reducers',
            'Software': 'software',
            'Filter': 'filters',
            'Accessory': 'accessories',
        }

        url = '%s/gear/%d#r%d' % (settings.ASTROBIN_BASE_URL, gear.id, review.id)
        recipients = [x.user for x in UserProfile.objects.filter(
            **{user_attr_lookup[gear_type]: gear})]
        notification = 'new_gear_review'

        push_notification(
            recipients, notification,
            {
                'url': url,
                'user': review.user,
            }
        )
       
        response_dict = {
            'success': True,
            'score': review.score,
            'content': review.content,
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype = 'application/javascript')

    return ajax_fail()


@require_POST
@login_required
def gear_comment_save(request):
    form = GearCommentForm(data = request.POST)

    if form.is_valid():
        author = User.objects.get(id = form.data['author'])
        gear, gear_type = get_correct_gear(form.data['gear_id'])
        if request.user != author:
            return HttpResponseForbidden()

        comment = form.save(commit = False)
        comment.author = author
        comment.gear = gear
        if form.data['parent_id'] != '':
            comment.parent = GearComment.objects.get(id = form.data['parent_id'])

        comment.save()

        user_attr_lookup = {
            'Telescope': 'telescopes',
            'Camera': 'cameras',
            'Mount': 'mounts',
            'FocalReducer': 'focal_reducers',
            'Software': 'software',
            'Filter': 'filters',
            'Accessory': 'accessories',
        }

        url = '%s/gear/%d#c%d' % (settings.ASTROBIN_BASE_URL, gear.id, comment.id)
        if not comment.parent:
            recipients = [x.user for x in UserProfile.objects.filter(
                **{user_attr_lookup[gear_type]: gear})]
            notification = 'new_gear_discussion'
        else:
            notification = 'new_comment_reply'
            recipients = [comment.parent.author]

        push_notification(
            recipients, notification,
            {
                'url': url,
                'user': author,
            }
        )
                
        response_dict = {
            'success': True,
            'comment_id': comment.id,
            'comment': comment.comment,
            'action': 'save',
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype = 'application/javascript')

    return ajax_fail()


@require_GET
@login_required
def gear_comment_delete(request, id):
    comment = get_object_or_404(GearComment, id = id)
    if comment.author != request.user:
        return HttpResponseForbidden()

    # NOTE: this function undeletes too!
    comment.is_deleted = not comment.is_deleted
    comment.save()

    response_dict = {
        'success': True,
        'deleted': comment.is_deleted,
        'comment': comment.comment,
    }
    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_GET
@login_required
def gear_comment_get(request, id):
    comment = get_object_or_404(GearComment, id = id)

    response_dict = {
        'success': True,
        'comment': comment.comment,
    }
    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_POST
@login_required
def gear_comment_edit(request):
    form = GearCommentForm(data = request.POST)

    if form.is_valid():
        author = User.objects.get(id = form.data['author'])
        gear = Gear.objects.get(id = form.data['gear_id'])
        if request.user != author:
            return HttpResponseForbidden()

        comment = GearComment.objects.get(id = form.data['parent_id'])
        comment.comment = form.cleaned_data['comment']
        comment.save()

        response_dict = {
            'success': True,
            'comment_id': comment.id,
            'comment': comment.comment,
            'action': 'edit',
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype = 'application/javascript')

    return ajax_fail()


@require_GET
def activities(request):
    return object_list(
        request, 
        queryset = Action.objects.all(),
        template_name = 'activities.html',
        template_object_name = 'global_action',
        paginate_by = 100,
        extra_context = {})


@require_POST
@login_required
@user_passes_test(lambda u: user_is_producer(u))
def commercial_products_claim(request, id):
    from templatetags.tags import gear_owners, gear_images

    def error(form):
        from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
        response_dict = {
            'form': as_bootstrap(form, 'horizontal') if form else '',
            'success': False,
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype = 'application/javascript')

    form = ClaimCommercialGearForm(data = request.POST, user = request.user)
    try:
        gear = Gear.objects.get(id = id)
        # Can't claim something that's already claimed:
        if gear.commercial:
            return error(form)
    except Gear.DoesNotExist:
        return error(form);

    # We need to add the choice to the field so that the form will validate.
    # If we don't, it won't validate because the selected option, which was
    # added via AJAX, is not among those available.
    form.fields['name'].choices += [(gear.id, gear.get_name())]
    if request.POST.get('merge_with'):
        merge_with = CommercialGear.objects.get(id = int(request.POST.get('merge_with')))
        proper_name = merge_with.proper_name if merge_with.proper_name else merge_with.gear_set.all()[0].get_name()
        form.fields['merge_with'].choices += [(merge_with.id, proper_name)]

    if not form.is_valid():
        return error(form)

    if form.cleaned_data['merge_with'] != '':
        commercial_gear = CommercialGear.objects.get(id = int(form.cleaned_data['merge_with']))
    else:
        commercial_gear = CommercialGear(
            producer = request.user,
            proper_name = gear.get_name(),
        )
        commercial_gear.save()

    gear.commercial = commercial_gear
    gear.save()

    claimed_gear = Gear.objects.filter(commercial = commercial_gear).values_list('id', flat = True)
    return HttpResponse(
        simplejson.dumps({
            'success': True,
            'id': commercial_gear.id,
            'claimed_gear_id': gear.id,
            'gear_ids': u','.join(str(x) for x in claimed_gear),
            'gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
            'make': gear.get_make(),
            'name': gear.get_name(),
            'owners': gear_owners(gear),
            'images': gear_images(gear),
            'is_merge': form.cleaned_data['merge_with'] != '',
        }),
        mimetype = 'application/javascript')



@require_GET
@login_required
@user_passes_test(lambda u: user_is_producer(u))
def commercial_products_unclaim(request, id):
    try:
        gear = Gear.objects.get(id = id)
    except Gear.DoesNotExist:
        return HttpResponseForbidden()

    commercial = gear.commercial
    commercial_id = commercial.id
    commercial_was_removed = False

    if commercial is None or commercial.producer != request.user:
        return HttpResponseForbidden()

    all_gear = Gear.objects.filter(commercial = commercial)
    if all_gear.count() == 1:
        commercial.delete()
        commercial_was_removed = True

    gear.commercial = None
    gear.save()

    if commercial_was_removed:
        claimed_gear = []
    else:
        claimed_gear = Gear.objects.filter(commercial = commercial).values_list('id', flat = True)

    return HttpResponse(
        simplejson.dumps({
            'success': True,
            'gear_id': id,
            'commercial_id': commercial_id,
            'commercial_was_removed': commercial_was_removed,
            'claimed_gear_ids': u','.join(str(x) for x in claimed_gear),
            'claimed_gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
        }),
        mimetype = 'application/javascript')


@require_GET
@login_required
@user_passes_test(lambda u: user_is_producer(u))
def commercial_products_merge(request, from_id, to_id):
    if from_id != to_id:
        try:
            from_cg = CommercialGear.objects.get(id = int(from_id))
            to_cg = CommercialGear.objects.get(id = int(to_id))
        except CommercialGear.DoesNotExist:
            return HttpResponseForbidden()

        if from_cg.producer != request.user or to_cg.producer != request.user:
            return HttpResponseForbidden()

        Gear.objects.filter(commercial = from_cg).update(commercial = to_cg)
        from_cg.delete()

        claimed_gear = Gear.objects.filter(commercial = to_cg).values_list('id', flat = True)

        return HttpResponse(
            simplejson.dumps({
                'success': True,
                'claimed_gear_ids': u','.join(str(x) for x in claimed_gear),
                'claimed_gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
            }),
            mimetype = 'application/javascript')

    return HttpResponse(
        simplejson.dumps({
            'success': False,
            'message': _("You can't merge a product to itself."),
        }),
        mimetype = 'application/javascript')

            
@require_GET
@login_required
@user_passes_test(lambda u: user_is_producer(u))
def commercial_products_edit(request, id):
    product = get_object_or_404(CommercialGear, id = id)
    if product.producer != request.user:
        return HttpResponseForbidden()

    form = CommercialGearForm(instance = product, user = request.user)

    return render_to_response(
        'commercial/products/edit.html',
        {
            'form': form,
            'product': product,
            'gear': Gear.objects.filter(commercial = product)[0],
        },
        context_instance = RequestContext(request))


@require_POST
@login_required
@user_passes_test(lambda u: user_is_producer(u))
def commercial_products_save(request, id):
    product = get_object_or_404(CommercialGear, id = id)
    if product.producer != request.user:
        return HttpResponseForbidden()

    form = CommercialGearForm(
        data = request.POST,
        instance = product,
        user = request.user)

    if form.is_valid():
        form.save()
        messages.success(request, _("Form saved. Thank you!"))
        return HttpResponseRedirect('/commercial/products/edit/%i/' % product.id)

    return render_to_response(
        'commercial/products/edit.html',
        {
            'form': form,
            'product': product,
            'gear': Gear.objects.filter(commercial = product)[0],
        },
        context_instance = RequestContext(request))


@require_POST
@login_required
@user_passes_test(lambda u: user_is_retailer(u))
def retailed_products_claim(request, id):
    from templatetags.tags import gear_owners, gear_images

    def error(form):
        from bootstrap_toolkit.templatetags.bootstrap_toolkit import as_bootstrap
        response_dict = {
            'form': as_bootstrap(form, 'horizontal') if form else '',
            'success': False,
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype = 'application/javascript')

    form = ClaimRetailedGearForm(data = request.POST, user = request.user)
    try:
        gear = Gear.objects.get(id = id)
        # Here, instead, we can claim something that's already claimed!
    except Gear.DoesNotExist:
        return error(form);

    # We need to add the choice to the field so that the form will validate.
    # If we don't, it won't validate because the selected option, which was
    # added via AJAX, is not among those available.
    form.fields['name'].choices += [(gear.id, gear.get_name())]
    if request.POST.get('merge_with'):
        merge_with = RetailedGear.objects.get(id = int(request.POST.get('merge_with')))
        proper_name = merge_with.gear_set.all()[0].get_name()
        form.fields['merge_with'].choices += [(merge_with.id, proper_name)]

    if not form.is_valid():
        return error(form)

    if form.cleaned_data['merge_with'] != '':
        retailed_gear = RetailedGear.objects.get(id = int(form.cleaned_data['merge_with']))
    else:
        retailed_gear = RetailedGear(
            retailer = request.user,
        )
        retailed_gear.save()

    gear.retailed.add(retailed_gear)
    gear.save()

    claimed_gear = Gear.objects.filter(retailed = retailed_gear).values_list('id', flat = True)
    return HttpResponse(
        simplejson.dumps({
            'success': True,
            'id': retailed_gear.id,
            'claimed_gear_id': gear.id,
            'gear_ids': u','.join(str(x) for x in claimed_gear),
            'gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
            'make': gear.get_make(),
            'name': gear.get_name(),
            'owners': gear_owners(gear),
            'images': gear_images(gear),
            'is_merge': form.cleaned_data['merge_with'] != '',
        }),
        mimetype = 'application/javascript')   


@require_GET
@login_required
@user_passes_test(lambda u: user_is_retailer(u))
def retailed_products_unclaim(request, id):
    try:
        gear = Gear.objects.get(id = id)
    except Gear.DoesNotExist:
        return HttpResponseForbidden()

    try:
        retailed = RetailedGear.objects.get(retailer = request.user, gear = gear)
    except RetailedGear.DoesNotExist:
        return HttpResponseForbidden()

    retailed_id = retailed.id
    retailed_was_removed = False

    if retailed is None or retailed.retailer != request.user:
        return HttpResponseForbidden()

    all_gear = Gear.objects.filter(retailed = retailed)
    if all_gear.count() == 1:
        retailed.delete()
        retailed_was_removed = True

    gear.retailed.remove(retailed)

    if retailed_was_removed:
        claimed_gear = []
    else:
        claimed_gear = Gear.objects.filter(retailed = retailed).values_list('id', flat = True)

    return HttpResponse(
        simplejson.dumps({
            'success': True,
            'gear_id': id,
            'retailed_id': retailed_id,
            'retailed_was_removed': retailed_was_removed,
            'claimed_gear_ids': u','.join(str(x) for x in claimed_gear),
            'claimed_gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
        }),
        mimetype = 'application/javascript')


@require_GET
@login_required
@user_passes_test(lambda u: user_is_retailer(u))
def retailed_products_merge(request, from_id, to_id):
    if from_id != to_id:
        try:
            from_rg = RetailedGear.objects.get(id = int(from_id))
            to_rg = RetailedGear.objects.get(id = int(to_id))
        except RetailedGear.DoesNotExist:
            return HttpResponseForbidden()

        if from_rg.retailer != request.user or to_rg.retailer != request.user:
            return HttpResponseForbidden()

        all_gear = Gear.objects.filter(retailed = from_rg)
        for g in all_gear:
            g.retailed.add(to_rg)

        from_rg.delete()

        claimed_gear = Gear.objects.filter(retailed = to_rg).values_list('id', flat = True)

        return HttpResponse(
            simplejson.dumps({
                'success': True,
                'claimed_gear_ids': u','.join(str(x) for x in claimed_gear),
                'claimed_gear_ids_links': u', '.join('<a href="/gear/%s/">%s</a>' % (x, x) for x in claimed_gear),
            }),
            mimetype = 'application/javascript')

    return HttpResponse(
        simplejson.dumps({
            'success': False,
            'message': _("You can't merge a product to itself."),
        }),
        mimetype = 'application/javascript')


@login_required
@user_passes_test(lambda u: user_is_retailer(u))
def retailed_products_edit(request, id):
    product = get_object_or_404(RetailedGear, id = id)
    if product.retailer != request.user:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = RetailedGearForm(data = request.POST, instance = product)

        if form.is_valid():
            form.save()
            messages.success(request, _("Form saved. Thank you!"))
            return HttpResponseRedirect('/commercial/products/retailed/edit/%i/' % product.id)
    else:
        form = RetailedGearForm(instance = product)

    return render_to_response(
        'commercial/products/retailed/edit.html',
        {
            'form': form,
            'product': product,
            'gear': Gear.objects.filter(retailed = product)[0],
        },
        context_instance = RequestContext(request))


@require_GET
def comments(request):
    return object_list(
        request, 
        queryset = Comment.objects.all().filter(is_deleted = False, image__is_wip = False).order_by('-added'),
        template_name = 'comments.html',
        template_object_name = 'comment',
        paginate_by = 100,
        extra_context = {
            's3_url': settings.S3_URL,
            'bucket_name': settings.AWS_STORAGE_BUCKET_NAME,
        })


@require_GET
def reviews(request):
    return object_list(
        request, 
        queryset = ReviewedItem.objects.all().order_by('-date_added'),
        template_name = 'reviews.html',
        template_object_name = 'review',
        paginate_by = 100,
        extra_context = {
        })

