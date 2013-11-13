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
from django.contrib.contenttypes.models import ContentType
from django.template import RequestContext
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.db import IntegrityError
from django.utils.translation import ugettext as _
from django.forms.models import formset_factory, inlineformset_factory
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.encoding import smart_str, smart_unicode
from django.utils.functional import curry
from django.utils.hashcompat import md5_constructor
from django.utils.http import urlquote

from haystack.query import SearchQuerySet, SQ
import persistent_messages
from reviews.forms import ReviewedItemForm
from actstream import action as act
from actstream.models import Action
from registration.forms import RegistrationForm
from zinnia.models import Entry
from endless_pagination.decorators import page_template

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

from nested_comments.models import NestedComment
from rawdata.forms import PublicDataPool_SelectExistingForm, PrivateSharedFolder_SelectExistingForm
from rawdata.models import PrivateSharedFolder

from models import *
from forms import *
from management import NOTICE_TYPES
from notifications import *
from notification.models import NoticeSetting, NOTICE_MEDIA_DEFAULTS
from shortcuts import *
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
    return datetime.now().replace(tzinfo=pytz.timezone(settings.TIME_ZONE)).astimezone(pytz.timezone(settings.TIME_ZONE))


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


# VIEWS

@page_template('index/stream_page.html', key = 'stream_page')
@page_template('index/recent_images_page.html',   key = 'recent_images_page')
def index(request, template = 'index/root.html', extra_context = None):
    """Main page"""
    from django.core.cache import cache

    image_ct = ContentType.objects.get_for_model(Image)
    image_rev_ct = ContentType.objects.get_for_model(ImageRevision)
    user_ct = ContentType.objects.get_for_model(User)

    recent_images = Image.objects.exclude(Q(title = None) | Q(title = ''))

    response_dict = {
        'registration_form': RegistrationForm(),
        'recent_images': recent_images,
        'recent_images_alias': 'thumb',
        'recent_images_batch_size': 55,
    }


    profile = None
    if request.user.is_authenticated():
        profile = request.user.userprofile

        section = request.GET.get('s')
        if section is None:
            section = profile.default_frontpage_section
        response_dict['section'] = section

        response_dict['recent_images_batch_size'] = 64

        try:
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
        except IndexError:
            # The is no IOTD
            pass

        response_dict['recent_commercial_gear'] =\
            [x for x in Image.objects.exclude(featured_gear = None) if x.featured_gear.all()[0].is_paid()]


        if section == 'global':
            ##################
            # GLOBAL ACTIONS #
            ##################
            actions = Action.objects.all().prefetch_related(
                'actor__userprofile',
                'target_content_type',
                'target')
            response_dict['actions'] = actions
            response_dict['cache_prefix'] = 'astrobin_global_actions'

        elif section == 'personal':
            ####################
            # PERSONAL ACTIONS #
            ####################
            cache_key = 'astrobin_users_image_ids_%s' % request.user
            users_image_ids = cache.get(cache_key)
            if users_image_ids is None:
                users_image_ids = [
                    str(x) for x in
                    Image.objects.filter(
                        user = request.user).values_list('id', flat = True)
                ]
                cache.set(cache_key, users_image_ids, 300)

            cache_key = 'astrobin_users_revision_ids_%s' % request.user
            users_revision_ids = cache.get(cache_key)
            if users_revision_ids is None:
                users_revision_ids = [
                    str(x) for x in
                    ImageRevision.objects.filter(
                        image__user = request.user).values_list('id', flat = True)
                ]
                cache.set(cache_key, users_revision_ids, 300)

            cache_key = 'astrobin_followed_user_ids_%s' % request.user
            followed_user_ids = cache.get(cache_key)
            if followed_user_ids is None:
                followed_user_ids = [
                    str(x) for x in
                    ToggleProperty.objects.filter(
                        property_type = "follow",
                        user = request.user,
                        content_type = ContentType.objects.get_for_model(User)
                    ).values_list('object_id', flat = True)
                ]
                cache.set(cache_key, followed_user_ids, 900)
            response_dict['has_followed_users'] = len(followed_user_ids) > 0

            cache_key = 'astrobin_followees_image_ids_%s' % request.user
            followees_image_ids = cache.get(cache_key)
            if followees_image_ids is None:
                followees_image_ids = [
                    str(x) for x in
                    Image.objects.filter(user_id__in = followed_user_ids).values_list('id', flat = True)
                ]
                cache.set(cache_key, followees_image_ids, 900)

            actions = Action.objects\
                .prefetch_related(
                    'actor__userprofile',
                    'target_content_type',
                    'target'
                ).filter(
                    # Actor is user, or...
                    Q(
                        Q(actor_content_type = user_ct) &
                        Q(actor_object_id = request.user.id)
                    ) |

                    # Action concerns user's images as target, or...
                    Q(
                        Q(target_content_type = image_ct) &
                        Q(target_object_id__in = users_image_ids)
                    ) |
                    Q(
                        Q(target_content_type = image_rev_ct) &
                        Q(target_object_id__in = users_revision_ids)
                    ) |

                    # Action concerns user's images as object, or...
                    Q(
                        Q(action_object_content_type = image_ct) &
                        Q(action_object_object_id__in = users_image_ids)
                    ) |
                    Q(
                        Q(action_object_content_type = image_rev_ct) &
                        Q(action_object_object_id__in = users_revision_ids)
                    ) |

                    # Actor is somebody the user follows, or...
                    Q(
                        Q(actor_content_type = user_ct) &
                        Q(actor_object_id__in = followed_user_ids)
                    ) |

                    # Action concerns an image by a followed user...
                    Q(
                        Q(target_content_type = image_ct) &
                        Q(target_object_id__in = followees_image_ids)
                    ) |
                    Q(
                        Q(action_object_content_type = image_ct) &
                        Q(action_object_object_id__in = followees_image_ids)
                    )
                )
            response_dict['actions'] = actions
            response_dict['cache_prefix'] = 'astrobin_personal_actions'

        elif section == 'followed':
            followed = [x.object_id for x in ToggleProperty.objects.filter(
                property_type = "follow",
                content_type = ContentType.objects.get_for_model(User),
                user = request.user)]

            response_dict['recent_images'] = recent_images.filter(user__in = followed)

        elif section == 'liked':
            response_dict['recent_images'] = \
                Image.objects.raw(
                    "DROP TABLE IF EXISTS recently_liked_to_show;" +
                    "CREATE TEMPORARY TABLE recently_liked_to_show ( object_id INT PRIMARY KEY, created TIMESTAMP);" +
                    "INSERT INTO recently_liked_to_show " +
                        "SELECT object_id::int, MAX(created_on) AS max_created_on " +
                        "FROM toggleproperties_toggleproperty " +
                        "WHERE property_type = 'like' " +
                        "AND content_type_id = " + str(image_ct.id) + " " +
                        "GROUP BY object_id " +
                        "ORDER BY max_created_on DESC " +
                        "LIMIT 320;" +
                    "SELECT astrobin_image.* " +
                    "FROM astrobin_image " +
                    "JOIN recently_liked_to_show ON id = object_id " +
                    "WHERE astrobin_image.is_wip = false " +
                    "ORDER BY recently_liked_to_show.created DESC;"
                )

        elif section == 'bookmarked':
            image_ct = ContentType.objects.get(app_label = 'astrobin', model = 'image')
            response_dict['recent_images'] = \
                Image.objects.raw(
                    "DROP TABLE IF EXISTS recently_bookmarked_to_show;" +
                    "CREATE TEMPORARY TABLE recently_bookmarked_to_show ( object_id INT PRIMARY KEY, created TIMESTAMP) ON COMMIT DROP;" +
                    "INSERT INTO recently_bookmarked_to_show " +
                        "SELECT object_id::int, MAX(created_on) AS max_created_on " +
                        "FROM toggleproperties_toggleproperty " +
                        "WHERE property_type = 'bookmark' " +
                        "AND content_type_id = " + str(image_ct.id) + " " +
                        "GROUP BY object_id " +
                        "ORDER BY max_created_on DESC " +
                        "LIMIT 320;" +
                    "SELECT astrobin_image.* " +
                    "FROM astrobin_image " +
                    "JOIN recently_bookmarked_to_show ON id = object_id " +
                    "WHERE astrobin_image.is_wip = false " +
                    "ORDER BY recently_bookmarked_to_show.created DESC;"
                )

        elif section == 'fits':
            response_dict['recent_images'] = recent_images.exclude(
                Q(link_to_fits = None) |
                Q(link_to_fits = ''))

    if extra_context is not None:
        response_dict.update(extra_context)

    return render_to_response(
        template, response_dict,
        context_instance = RequestContext(request))


@require_GET
def expore_choose(request):
    return render_to_response(
        'explore_choose.html', {},
        context_instance = RequestContext(request))


@require_GET
def wall(request):
    """The Big Wall"""
    sqs = SearchQuerySet().all().models(Image)

    response_dict = {}

    if request.GET.get('sort') == '-acquired':
        response_dict['sort'] = '-acquired'
        sqs = sqs.order_by('-last_acquisition_date')
    elif request.GET.get('sort') == '-views':
        response_dict['sort'] = '-views'
        sqs = sqs.order_by('-views');
    elif request.GET.get('sort') == '-likes':
        response_dict['sort'] = '-likes'
        sqs = sqs.order_by('-likes', '-likes')
    elif request.GET.get('sort') == '-bookmarks':
        response_dict['sort'] = '-bookmarks'
        sqs = sqs.order_by('-bookmarks')
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
    elif filter == 'products':
        sqs = sqs.filter(is_commercial = True)
    elif filter == 'other':
        sqs = sqs.filter(subject_type = 600)

    return object_list(
        request,
        queryset = sqs,
        template_name = 'wall.html',
        template_object_name = 'object',
        paginate_by = 70,
        extra_context = response_dict)


@require_GET
def iotd_archive(request):
    """Archive of 'Images of the day'"""

    queryset = ImageOfTheDay.objects.all()

    return object_list(
        request,
        queryset = queryset,
        template_name = 'iotd_archive.html',
        template_object_name = 'iotd',
        paginate_by = 30,
    )


@require_GET
def no_javascript(request):
    return render_to_response('no_javascript.html',
        context_instance=RequestContext(request))


@require_GET
def image_detail(request, id, r):
    """ Show details of an image"""
    image = get_object_or_404(
        Image.all_objects,
        pk = id)

    response_dict = {}

    # TODO: unify duplicated code with image_full

    ################################
    # REDIRECT TO CORRECT REVISION #
    ################################

    if r is None:
        r = request.GET.get('r')

    revisions = ImageRevision.objects\
        .select_related('image__user__userprofile')\
        .filter(image = image)

    if r is None and not image.is_final:
        final_revs = revisions.filter(is_final = True)
        # We should only have one
        if final_revs:
            final = revisions.filter(is_final = True)[0]
            return HttpResponseRedirect('/%i/%s/' % (image.id, final.label))

    if r is None:
        try:
            r = revisions.filter(is_final = True)[0].label
        except IndexError:
            r = 0


    revision_image = None
    instance_to_platesolve = image
    is_revision = False
    if r != 0:
        try:
            revision_image = ImageRevision.objects.filter(image = image, label = r)[0]
            instance_to_platesolve = revision_image
            is_revision = True
        except:
            pass


    #############################
    # GENERATE ACQUISITION DATA #
    #############################
    from moon import MoonPhase;

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



    profile = None
    if request.user.is_authenticated():
        profile = request.user.userprofile


    ##############
    # BASIC DATA #
    ##############

    updated_on = to_user_timezone(image.updated, profile) if profile else image.updated
    alias = 'regular'
    mod = request.GET.get('mod')
    if mod == 'inverted':
        alias = 'regular_inverted'

    subjects = image.objects_in_field.split(',') if image.objects_in_field else ''
    skyplot_zoom1 = None

    if is_revision:
        if revision_image.solution:
            if revision_image.solution.objects_in_field:
               subjects = revision_image.solution.objects_in_field.split(',')
            if revision_image.solution.skyplot_zoom1:
                skyplot_zoom1 = revision_image.solution.skyplot_zoom1
    else:
        if image.solution:
            if image.solution.objects_in_field:
                subjects = image.solution.objects_in_field.split(',')
            if image.solution.skyplot_zoom1:
                skyplot_zoom1 = image.solution.skyplot_zoom1

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



    ######################
    # PREFERRED LANGUAGE #
    ######################

    preferred_language = image.user.userprofile.language
    if preferred_language:
        preferred_language = LANGUAGES[preferred_language]
    else:
        preferred_language = _("English")


    ##########################
    # LIKE / BOOKMARKED THIS #
    ##########################
    like_this = image.toggleproperties.filter(property_type = "like")
    bookmarked_this = image.toggleproperties.filter(property_type = "bookmark")


    #################
    # RESPONSE DICT #
    #################

    from astrobin_apps_platesolving.solver import Solver

    response_dict = dict(response_dict.items() + {
        'SHARE_PATH': settings.ASTROBIN_SHORT_BASE_URL,

        'alias': alias,
        'mod': mod,
        'revisions': revisions,
        'is_revision': is_revision,
        'revision_image': revision_image,
        'revision_label': r,

        'instance_to_platesolve': instance_to_platesolve,
        'show_solution': instance_to_platesolve.solution and instance_to_platesolve.solution.status == Solver.SUCCESS,
        'skyplot_zoom1': skyplot_zoom1,

        'image_ct': ContentType.objects.get_for_model(Image),
        'like_this': like_this,
        'bookmarked_this': bookmarked_this,
        'min_index_to_like': 1.00,

        'comments_number': NestedComment.objects.filter(
            deleted = False,
            content_type__app_label = 'astrobin',
            content_type__model = 'image',
            object_id = image.id).count(),
        'gear_list': gear_list,
        'gear_list_has_commercial': gear_list_has_commercial,
        'gear_list_has_paid_commercial': gear_list_has_paid_commercial,
        'image_type': image_type,
        'ssa': ssa,
        'deep_sky_data': deep_sky_data,
        # TODO: check that solved image is correcly laid on top
        'private_message_form': PrivateMessageForm(),
        'upload_revision_form': ImageRevisionUploadForm(),
        'dates_label': _("Dates"),
        'updated_on': updated_on,
        'show_contains': (image.subject_type == 100 and subjects) or (image.subject_type >= 200),
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

        'solar_system_main_subject_id': image.solar_system_main_subject,
        'solar_system_main_subject': SOLAR_SYSTEM_SUBJECT_CHOICES[image.solar_system_main_subject][1] if image.solar_system_main_subject is not None else None,
        'content_type': ContentType.objects.get(app_label = 'astrobin', model = 'image'),
        'preferred_language': preferred_language,
        'select_datapool_form': PublicDataPool_SelectExistingForm(),
        'select_sharedfolder_form': PrivateSharedFolder_SelectExistingForm(user = request.user) if request.user.is_authenticated() else None,
        'has_sharedfolders': PrivateSharedFolder.objects.filter(
            Q(creator = request.user) |
            Q(users = request.user)).count() > 0 if request.user.is_authenticated() else False,

        'iotd_date': image.iotd_date()
    }.items())

    return object_detail(
        request,
        queryset = Image.all_objects.all(),
        object_id = id,
        template_name = 'image/detail.html',
        template_object_name = 'image',
        extra_context = response_dict)


@login_required
@require_POST
def image_flag_thumbs(request, id):
    image = get_object_or_404(Image.all_objects, id = id)
    image.thumbnail_invalidate_all()
    messages.success(request, _("Thanks for reporting the problem. All thumbnails will be generated again."))
    return HttpResponseRedirect(reverse("image_detail", kwargs= {'id': id}))


@require_GET
def image_thumb(request, id, r, alias):
    image = get_object_or_404(Image.all_objects, id = id)

    url = settings.IMAGES_URL + image.image_file.name
    if 'animated' not in request.GET:
        url = image.thumbnail(alias, {
            'revision_label': r,
        })

    return HttpResponse(
        simplejson.dumps({
            'id': id,
            'url': url,
        }))


@require_GET
def image_rawthumb(request, id, r, alias):
    image = get_object_or_404(Image.all_objects, id = id)
    url = image.thumbnail(alias, {
        'revision_label': r,
    })

    return HttpResponseRedirect(url)


@require_GET
def image_full(request, id, r):
    image = get_object_or_404(Image.all_objects, pk=id)

    ################################
    # REDIRECT TO CORRECT REVISION #
    ################################

    if r is None:
        r = request.GET.get('r')

    revisions = ImageRevision.objects.filter(image = image)

    if r is None and not image.is_final:
        final_revs = revisions.filter(is_final = True)
        # We should only have one
        if final_revs:
            final = revisions.filter(is_final = True)[0]
            return HttpResponseRedirect('/full/%i/%s/' % (image.id, final.label))

    if r is None:
        try:
            r = revisions.filter(is_final = True)[0].label
        except IndexError:
            r = 0


    mod = None
    if 'mod' in request.GET and request.GET['mod'] == 'inverted':
        mod = 'inverted'

    real = 'real' in request.GET
    if real:
        alias = 'real'
    else:
        alias = 'hd'

    if mod:
        alias += "_%s" % mod

    return object_detail(
        request,
        queryset = Image.all_objects.all(),
        object_id = id,
        template_name = 'image/full.html',
        template_object_name = 'image',
        extra_context = {
            'real': real,
            'alias': alias,
            'mod': mod,
            'revision_label': r,
        })


@login_required
def image_upload(request):
    from rawdata.utils import (
        user_has_subscription,
        user_has_active_subscription,
        user_has_inactive_subscription,
        user_is_over_limit,
        user_byte_limit,
        user_used_percent,
        user_progress_class,
        supported_raw_formats,
    )

    has_sub       = user_has_subscription(request.user)
    has_act_sub   = has_sub and user_has_active_subscription(request.user)
    has_inact_sub = has_sub and user_has_inactive_subscription(request.user)
    is_over_limit = has_act_sub and user_is_over_limit(request.user)

    response_dict = {
        'upload_form': ImageUploadForm(),
        'has_sub': has_sub,
        'has_act_sub': has_act_sub,
        'has_inact_sub': has_inact_sub,
        'is_over_limit': is_over_limit,

        'byte_limit': user_byte_limit(request.user) if has_sub else 0,
        'used_percent': user_used_percent(request.user) if has_sub else 100,
        'progress_class': user_progress_class(request.user) if has_sub else '',
        'supported_raw_formats': supported_raw_formats(),
    }

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

    if settings.READONLY_MODE:
        messages.error(request, _("AstroBin is currently in read-only mode, because of server maintenance. Please try again soon!"));
        return HttpResponseRedirect('/upload/')

    if 'image_file' not in request.FILES:
        return upload_error()

    form = ImageUploadForm(request.POST, request.FILES)

    if not form.is_valid():
        return upload_error()

    image_file = request.FILES["image_file"]
    ext = os.path.splitext(image_file.name)[1].lower()

    if ext not in ('.jpg', '.jpeg', '.png', '.gif'):
        return upload_error()

    try:
        from PIL import Image as PILImage
        trial_image = PILImage.open(image_file)
        trial_image.verify()

        if ext == '.png' and trial_image.mode == 'I':
            messages.warning(request, _("You uploaded an Indexed PNG file. AstroBin will need to lower the color count to 256 in order to work with it."))
    except:
        return upload_error()

    profile = request.user.userprofile
    image = form.save(commit = False)
    image.user = request.user
    image.license = profile.default_license

    if 'wip' in request.POST:
        image.is_wip = True

    image.image_file.file.seek(0) # Because we opened it with PIL
    image.save()

    return HttpResponseRedirect(reverse('image_edit_watermark', kwargs={'id': image.id}))


@login_required
@require_GET
def image_edit_basic(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    form = ImageEditBasicForm(user = image.user, instance = image)

    return render_to_response('image/edit/basic.html',
        {'image':image,
         'form':form,
        },
        context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_watermark(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user:
        return HttpResponseForbidden()

    profile = image.user.userprofile
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
    image = Image.all_objects.get(pk=id)
    profile = image.user.userprofile
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    no_gear = True
    if profile.telescopes and profile.cameras:
        no_gear = False

    form = ImageEditGearForm(user=image.user, instance=image)
    response_dict = {
        'form': form,
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

    from astrobin_apps_platesolving.solver import Solver

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
    if edit_type == 'deep_sky' or (image.solution and image.solution.status != Solver.FAILED):
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
            profile = image.user.userprofile
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
    try:
        image_id = request.POST['image_id']
    except MultiValueDictKeyError:
        raise Http404


    image = Image.all_objects.get(pk=image_id)
    form = ImageEditBasicForm(user = image.user, data=request.POST, instance=image)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if not form.is_valid():
        response_dict = {
            'image': image,
            'form': form,
        }

        return render_to_response("image/edit/basic.html",
            response_dict,
            context_instance=RequestContext(request))

    form.save()


    if 'submit_gear' in request.POST:
        return HttpResponseRedirect(reverse('image_edit_gear', kwargs={'id': image.id}))
    else:
        messages.success(request, _("Form saved. Thank you!"))
        return HttpResponseRedirect(image.get_absolute_url())


@login_required
@require_POST
def image_edit_save_watermark(request):
    try:
        image_id = request.POST['image_id']
    except MultiValueDictKeyError:
        raise Http404

    image = get_object_or_404(Image, pk=image_id)
    if request.user != image.user:
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
    profile = image.user.userprofile
    profile.default_watermark = form.cleaned_data['watermark']
    profile.default_watermark_text = form.cleaned_data['watermark_text']
    profile.default_watermark_position = form.cleaned_data['watermark_position']
    profile.default_watermark_opacity = form.cleaned_data['watermark_opacity']
    profile.save()

    if 'submit_next' in request.POST:
        return HttpResponseRedirect(reverse('image_edit_basic', kwargs={'id': image.id}))

    return HttpResponseRedirect(image.get_absolute_url())


@login_required
@require_POST
def image_edit_save_gear(request):
    try:
        image_id = request.POST['image_id']
    except MultiValueDictKeyError:
        raise Http404

    image = Image.all_objects.get(pk=image_id)
    profile = image.user.userprofile
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
    }

    if not form.is_valid():
        return render_to_response("image/edit/gear.html",
            response_dict,
            context_instance=RequestContext(request))
    form.save()

    response_dict['image'] = image

    if 'submit_acquisition' in request.POST:
        return HttpResponseRedirect(reverse('image_edit_acquisition', kwargs={'id': image.id}))

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect(image.get_absolute_url())


@login_required
@require_POST
def image_edit_save_acquisition(request):
    try:
        image_id = request.POST['image_id']
    except MultiValueDictKeyError:
        raise Http404

    image = Image.all_objects.get(pk=image_id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    edit_type = request.POST.get('edit_type')
    advanced = request.POST['advanced'] if 'advanced' in request.POST else False
    advanced = True if advanced == 'true' else False

    response_dict = {
        'image': image,
        'edit_type': edit_type,
    }

    dsa_qs = DeepSky_Acquisition.objects.filter(image=image)
    solar_system_acquisition = None

    for a in SolarSystem_Acquisition.objects.filter(image=image):
        a.delete()

    if edit_type == 'deep_sky' or image.solution:
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
                    profile = image.user.userprofile
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

    messages.success(request, _("Form saved. Thank you!"))
    return HttpResponseRedirect(image.get_absolute_url())


@login_required
@require_POST
def image_edit_save_license(request):
    try:
        image_id = request.POST['image_id']
    except MultiValueDictKeyError:
        raise Http404

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
    return HttpResponseRedirect(image.get_absolute_url())


@login_required
@require_POST
def image_delete(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    image.thumbnail_invalidate_all()
    image.delete()
    messages.success(request, _("Image deleted."));
    return HttpResponseRedirect(request.user.get_absolute_url());


@login_required
@require_POST
def image_delete_revision(request, id):
    revision = get_object_or_404(ImageRevision, pk=id)
    image = revision.image
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if revision.is_final:
        image.is_final = True
        image.save()

    image.thumbnail_invalidate_all()
    revision.delete()
    messages.success(request, _("Revision deleted."));

    return HttpResponseRedirect("/%i/" % image.id);


@login_required
@require_POST
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

    image.image_file = final.image_file
    image.updated = final.uploaded

    image.w = final.w
    image.h = final.h

    image.is_final = True

    if image.solution:
        image.solution.delete()

    image.save()

    if final.solution:
        # Get the solution this way, I don't know why it wouldn't work otherwise
        content_type = ContentType.objects.get_for_model(ImageRevision)
        solution = Solution.objects.get(content_type = content_type, object_id = final.pk)
        solution.content_object = image
        solution.save()

    image.thumbnail_invalidate_all()
    final.delete()

    messages.success(request, _("Image deleted."));
    return HttpResponseRedirect("/%i/" % image.id);


@login_required
@require_GET
def image_promote(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    profile = request.user.userprofile

    if image.is_wip:
        image.is_wip = False
        image.save()

        followers = [
            x.user for x in
            ToggleProperty.objects.toggleproperties_for_object("follow", User.objects.get(pk = request.user.pk))
        ]
        push_notification(followers, 'new_image',
            {
                'originator': request.user,
                'object_url': settings.ASTROBIN_BASE_URL + image.get_absolute_url()
            })

        verb = "uploaded a new image"
        act.send(image.user, verb = verb, action_object = image)

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
    profile = user.userprofile
    user_ct = ContentType.objects.get_for_model(User)

    viewer_profile = None
    if request.user.is_authenticated():
        viewer_profile = request.user.userprofile

    section = 'public'
    subsection = request.GET.get('sub', 'year')
    active = request.GET.get('active')
    menu = []

    qs = Image.objects.filter(user = user)

    if 'staging' in request.GET:
        if request.user != user:
            return HttpResponseForbidden()
        qs = Image.wip.filter(user = user)
        section = 'staging'
        subsection = None
    else:
        ############
        # UPLOADED #
        ############
        if subsection == 'uploaded':
            # All good already
            pass

        ############
        # ACQUIRED #
        ############
        elif subsection == 'acquired':
            lad_sql = 'SELECT date FROM astrobin_acquisition '\
                      'WHERE date IS NOT NULL AND image_id = astrobin_image.id '\
                      'ORDER BY date DESC '\
                      'LIMIT 1'
            qs = qs.extra(select = {'last_acquisition_date': lad_sql},
                            order_by = ['-last_acquisition_date'])

        ########
        # YEAR #
        ########
        elif subsection == 'year':
            acq = Acquisition.objects.filter(image__user = user, image__is_wip = False)
            if acq:
                years = sorted(list(set([a.date.year for a in acq if a.date])), reverse = True)
                nd = _("No date specified")
                menu = [(str(x), str(x)) for x in years] + [(0, nd)]

                if active == '0':
                    qs = qs.filter(
                        (Q(subject_type__lt = 500) | Q(subject_type = 600)) &
                        (Q(acquisition = None) | Q(acquisition__date = None))).distinct()
                else:
                    if active is None:
                        if years:
                            active = str(years[0])

                    if active:
                        qs = qs.filter(acquisition__date__year = active).distinct()

        ########
        # GEAR #
        ########
        elif subsection == 'gear':
            from templatetags.tags import gear_name

            telescopes = profile.telescopes.all()
            cameras = profile.cameras.all()

            nd = _("No imaging telescopes or lenses, or no imaging cameras specified")
            gi = _("Gear images")

            menu += [(x.id, gear_name(x)) for x in telescopes]
            menu += [(x.id, gear_name(x)) for x in cameras]
            menu += [( 0, nd)]
            menu += [(-1, gi)]

            if active == 0:
                qs = qs.filter(
                    (Q(subject_type = 100) | Q(subject_type = 200)) &
                    (Q(imaging_telescopes = None) | Q(imaging_cameras = None))).distinct()
            elif active == -1:
                qs = qs.filter(Q(subject_type = 500)).distinct()
            else:
                if active is None:
                    if telescopes:
                        active = telescopes[0].id
                if active:
                    qs = qs.filter(Q(imaging_telescopes__id = active) |
                                     Q(imaging_cameras__id = active)).distinct()

        ###########
        # SUBJECT #
        ###########
        elif subsection == 'subject':
            menu += [('DEEP', _("Deep sky"))]
            menu += [('SOLAR',  _("Solar system"))]
            menu += [('WIDE',   _("Extremely wide field"))]
            menu += [('TRAILS', _("Star trails"))]
            menu += [('GEAR', _("Gear"))]
            menu += [('OTHER', _("Other"))]
            menu += [('NOSUB', _("No subjects specified"))]

            if active is None:
                active = 'DEEP'

            if active == 'DEEP':
                qs = qs.filter(subject_type = 100)

            elif active == 'SOLAR':
                qs = qs.filter(solar_system_main_subject__gte = 0)

            elif active == 'WIDE':
                qs = qs.filter(subject_type = 300)

            elif active == 'TRAILS':
                qs = qs.filter(subject_type = 400)

            elif active == 'GEAR':
                qs = qs.filter(subject_type = 500)

            elif active == 'OTHER':
                qs = qs.filter(subject_type = 600)

            elif active == 'NOSUB':
                qs = qs.filter(
                    (Q(subject_type = 100) | Q(subject_type = 200)) &
                    (Q(objects_in_field = None)) &
                    (Q(solar_system_main_subject = None))).distinct()

        ###########
        # NO DATA #
        ###########
        elif subsection == 'nodata':
            k_list = []

            menu += [('SUB',  _("No subjects specified"))]
            menu += [('GEAR', _("No imaging telescopes or lenses, or no imaging cameras specified"))]
            menu += [('ACQ',  _("No acquisition details specified"))]

            if active is None:
                active = 'SUB'

            if active == 'SUB':
                qs =  qs.filter(
                    (Q(subject_type = 100) | Q(subject_type = 200)) &
                    (Q(objects_in_field = None)) &
                    (Q(solar_system_main_subject = None)))

            elif active == 'GEAR':
                qs = qs.filter(
                    Q(subject_type__lt = 500) &
                    (Q(imaging_telescopes = None) | Q(imaging_cameras = None)))

            elif active == 'ACQ':
                qs = qs.filter(
                    Q(subject_type__lt = 500) &
                    Q(acquisition = None))


    # Calculate some stats
    from django.template.defaultfilters import timesince

    member_since = None
    date_time = user.date_joined.replace(tzinfo = None)
    diff = abs(date_time - datetime.today())
    span = timesince(date_time)
    if span == "0 " + _("minutes"):
        member_since = _("seconds ago")
    else:
        member_since = _("%s ago") % span

    last_login = user.last_login
    if request.user.is_authenticated():
        viewer_profile = request.user.userprofile
        last_login = to_user_timezone(user.last_login, viewer_profile)

    followers = ToggleProperty.objects.toggleproperties_for_object("follow", user).count()
    following = ToggleProperty.objects.filter(
        property_type = "follow",
        user = user,
        content_type = user_ct).count()

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
        (_('Total integration time'), "%.1f %s" % (integration, _("hours"))),
        (_('Average integration time'), "%.1f %s" % (avg_integration, _("hours"))),
    )


    response_dict = {
        'followers': followers,
        'following': following,
        'image_list': qs,
        'sort': request.GET.get('sort'),
        'view': request.GET.get('view', 'default'),
        'user':user,
        'profile':profile,
        'private_message_form': PrivateMessageForm(),
        'section':section,
        'subsection':subsection,
        'active':active,
        'menu':menu,
        'stats':stats,
        'images_no': images,
        'alias':'gallery',
    }

    template_name = 'user/profile.html'
    if request.is_ajax():
        template_name = 'inclusion_tags/image_list_entries.html'

    return render_to_response(
        template_name, response_dict,
        context_instance = RequestContext(request))


@require_GET
def user_page_commercial_products(request, username):
    user = get_object_or_404(User, username = username)
    if user != request.user:
        return HttpResponseForbidden()

    profile = user.userprofile

    response_dict = {
        'user': user,
        'profile': profile,
        'user_is_producer': user_is_producer(user),
        'user_is_retailer': user_is_retailer(user),
        'commercial_gear_list': CommercialGear.objects.filter(producer = user).exclude(base_gear = None),
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
def user_page_bookmarks(request, username):
    user = get_object_or_404(User, username = username)

    image_ct = ContentType.objects.get(app_label = 'astrobin', model = 'image')
    images = \
        [x.content_object for x in \
         ToggleProperty.objects.toggleproperties_for_user("bookmark", user) \
            .filter(content_type = image_ct) \
            .order_by('-created_on')
        ]

    return render_to_response('user/bookmarks.html',
        {
            'user': user,
            'bookmarks': images,
            'private_message_form': PrivateMessageForm(),
        },
        context_instance = RequestContext(request)
    )


@require_GET
@page_template('astrobin_apps_users/inclusion_tags/user_list_entries.html', key = 'users_page')
def user_page_following(request, username, extra_context = None):
    user = get_object_or_404(User, username = username)

    user_ct = ContentType.objects.get_for_model(User)
    followed_users = [
        user_ct.get_object_for_this_type(pk = x.object_id) for x in
        ToggleProperty.objects.filter(
            property_type = "follow",
            user = user,
            content_type = user_ct)
    ]

    template_name = 'user/following.html'
    if request.is_ajax():
        template_name = 'astrobin_apps_users/inclusion_tags/user_list_entries.html'

    return render_to_response(template_name,
        {
            'request_user': User.objects.get(pk = request.user.pk) if request.user.is_authenticated() else None,
            'layout': 'inline',
            'user': user,
            'user_list': followed_users,
            'view': request.GET.get('view', 'default'),
            'STATIC_URL': settings.STATIC_URL,
            'private_message_form': PrivateMessageForm(),
        },
        context_instance = RequestContext(request)
    )


@require_GET
@page_template('astrobin_apps_users/inclusion_tags/user_list_entries.html', key = 'users_page')
def user_page_followers(request, username, extra_context = None):
    user = get_object_or_404(User, username = username)

    user_ct = ContentType.objects.get_for_model(User)
    followers = [
        x.user for x in
        ToggleProperty.objects.filter(
            property_type = "follow",
            object_id = user.pk,
            content_type = user_ct)
    ]

    template_name = 'user/followers.html'
    if request.is_ajax():
        template_name = 'astrobin_apps_users/inclusion_tags/user_list_entries.html'

    return render_to_response(template_name,
        {
            'request_user': User.objects.get(pk = request.user.pk) if request.user.is_authenticated() else None,
            'layout': 'inline',
            'user': user,
            'user_list': followers,
            'view': request.GET.get('view', 'default'),
            'STATIC_URL': settings.STATIC_URL,
            'private_message_form': PrivateMessageForm(),
        },
        context_instance = RequestContext(request)
    )


@require_GET
def user_page_plots(request, username):
    """Shows the user's public page"""
    user = get_object_or_404(User, username = username)
    profile = user.userprofile

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

    profile = user.userprofile
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
def user_profile_stats_get_views_ajax(request, username, period = 'monthly'):
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
def stats_get_image_views_ajax(request, id, period = 'monthly'):
    import stats as _s

    (label, data, options) = _s.image_views(id, period)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_get_gear_views_ajax(request, id, period = 'monthly'):
    import stats as _s

    (label, data, options) = _s.gear_views(id, period)

    response_dict = {
        'flot_label': label,
        'flot_data': data,
        'flot_options': options,
    }

    return ajax_response(response_dict)


@require_GET
def stats_get_affiliated_gear_views_ajax(request, username, period = 'monthly'):
    import stats as _s

    (label, data, options) = _s.affiliated_gear_views(username, period)

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
    profile = request.user.userprofile
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

    profile = request.user.userprofile
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
    profile = request.user.userprofile
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
    profile = request.user.userprofile
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
    profile = request.user.userprofile
    form = DefaultImageLicenseForm(instance = profile)
    return render_to_response(
        'user/profile/edit/license.html',
        {'form': form},
        context_instance = RequestContext(request))


@login_required
@require_POST
def user_profile_save_license(request):
    profile = request.user.userprofile
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
    profile = request.user.userprofile

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
    profile = request.user.userprofile
    gear, gear_type = get_correct_gear(id)
    if not gear:
        raise Http404

    profile.remove_gear(gear, gear_type)

    return ajax_success()


@login_required
@require_GET
def user_profile_edit_locations(request):
    profile = request.user.userprofile
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
    profile = request.user.userprofile
    LocationsFormset = inlineformset_factory(
        UserProfile, Location, form = LocationEditForm, extra = 1)
    formset = LocationsFormset(data = request.POST, instance = profile)
    if not formset.is_valid():
        messages.error(request, _("There was one or more errors processing the form. You may need to scroll down to see them."))
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

    profile = request.user.userprofile

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
    from django.core.files import File
    from django.core.files.temp import NamedTemporaryFile

    response_dict = {
        'readonly': settings.READONLY_MODE
    }

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

                    img = NamedTemporaryFile(delete=True)
                    img.write(urllib2.urlopen(source).read())
                    img.flush()
                    img.seek(0)
                    f = File(img)


                    profile = request.user.userprofile
                    image = Image(image_file = f,
                                  user=request.user,
                                  title=title if title is not None else '',
                                  description=description if description is not None else '',
                                  subject_type = 600, # Default to Other only when doing a Flickr import
                                  license = profile.default_license)
                    image.save()

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
@require_POST
def user_profile_seen_realname(request):
    profile = request.user.userprofile
    profile.seen_realname = True
    profile.save()

    return HttpResponseRedirect(request.POST.get('next', '/'))


@login_required
@require_GET
def user_profile_edit_preferences(request):
    """Edits own preferences"""
    profile = request.user.userprofile
    form = UserProfileEditPreferencesForm(instance=profile)
    response_dict = {
        'form': form,
    }
    email_medium = 0 # see NOTICE_MEDIA in notifications/models.py
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

    profile = request.user.userprofile
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
        email_medium = 0 # see NOTICE_MEDIA in notifications/models.py
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
    try:
        image_id = request.POST['image_id']
    except MultiValueDictKeyError:
        raise Http404

    form = BringToAttentionForm(data=request.POST)
    image = get_object_or_404(Image, id=image_id)

    response_dict = {
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
        try:
            user = User.objects.get(username=username)
            recipients.append(user)
        except User.DoesNotExist:
            pass

    push_notification(recipients, 'attention_request',
                      {'object':image,
                       'object_url':settings.ASTROBIN_BASE_URL + image.get_absolute_url(),
                       'originator':request.user.userprofile,
                       'originator_url': request.user.get_absolute_url()})

    return HttpResponseRedirect('/%d/bring-to-attention/complete/' % image.id)


@login_required
@require_GET
def bring_to_attention_complete(request, id):
    image = get_object_or_404(Image, id=id)

    response_dict = {
        'image': image,
    }
    return render_to_response(
        'image/actions/bring_to_attention_complete.html',
        response_dict,
        context_instance = RequestContext(request))


@login_required
@require_POST
def image_revision_upload_process(request):
    # TODO: unify Image and ImageRevision
    def upload_error(image):
        messages.error(request, _("Invalid image or no image provided. Allowed formats are JPG, PNG and GIF."))
        return HttpResponseRedirect(image.get_absolute_url())

    try:
        image_id = request.POST['image_id']
    except MultiValueDictKeyError:
        raise Http404

    image = Image.all_objects.get(id=image_id)

    if settings.READONLY_MODE:
        messages.error(request, _("AstroBin is currently in read-only mode, because of server maintenance. Please try again soon!"));
        return HttpResponseRedirect(image.get_absolute_url())

    form = ImageRevisionUploadForm(request.POST, request.FILES)

    if not form.is_valid():
        return upload_error(image)

    image_file = request.FILES["image_file"]
    ext = os.path.splitext(image_file.name)[1].lower()

    if ext not in ('.jpg', '.jpeg', '.png', '.gif'):
        return upload_error(image)

    try:
        from PIL import Image as PILImage
        trial_image = PILImage.open(image_file)
        trial_image.verify()

        if ext == '.png' and trial_image.mode == 'I':
            messages.warning(request, _("You uploaded an Indexed PNG file. AstroBin will need to lower the color count to 256 in order to work with it."))
    except:
        return upload_error(image)

    revisions = ImageRevision.objects.filter(image = image).order_by('id')
    highest_label = 'A'
    for r in revisions:
        r.is_final = False
        r.save()
        highest_label = r.label

    image.is_final = False
    image.save()

    image_revision = form.save(commit = False)
    image_revision.user = request.user
    image_revision.image = image
    image_revision.is_final = True
    image_revision.label = base26_encode(ord(highest_label) - ord('A') + 1)

    image_revision.image_file.file.seek(0) # Because we opened it with PIL
    image_revision.save()

    messages.success(request, _("Image uploaded. Thank you!"))
    return HttpResponseRedirect(image_revision.get_absolute_url())


@require_GET
@user_passes_test(lambda u: u.is_superuser)
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

    if 'page' in request.GET:
        raise Http404

    sqs = SearchQuerySet()
    sort = '-normalized_likes'
    if 'sort' in request.GET:
        sort = request.GET.get('sort')
        if sort == 'likes':
            sort = '-normalized_likes'
        elif sort == 'followers':
            sort = '-followers'
        elif sort == 'integration':
            sort = '-integration'
        elif sort == 'images':
            sort = '-images'
        else:
            sort = '-normalized_likes'

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
            .filter(
                Q(user__groups__name = 'Paying'))
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
def help_questions(request):
    return render_to_response('questions.html',
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
        profile = request.user.userprofile
        profile.language = lang
        profile.save()

    return response


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

    profile = request.user.userprofile
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
@never_cache
def gear_popover_ajax(request, id):
    gear, gear_type = get_correct_gear(id)
    profile = request.user.userprofile \
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

    html = render_to_string(template,
        {
            'request': request,
            'user': request.user,
            'gear': gear,
            'is_authenticated': request.user.is_authenticated(),
            'IMAGES_URL': settings.IMAGES_URL,
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
    profile = request.user.userprofile \
              if request.user.is_authenticated() \
              else None

    from django.template.defaultfilters import timesince

    member_since = None
    date_time = user.date_joined.replace(tzinfo = None)
    diff = abs(date_time - datetime.today())
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
            'is_authenticated': request.user.is_authenticated(),
            'request': request,
        })

    response_dict = {
        'success': True,
        'html': html,
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


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

    all_images = Image.by_gear(gear, gear_type).filter(is_wip = False)

    show_commercial = (gear.commercial and gear.commercial.is_paid()) or (gear.commercial and gear.commercial.producer == request.user)

    return object_detail(
        request,
        queryset = Gear.objects.all(),
        object_id = id,
        template_name = 'gear/page.html',
        template_object_name = 'gear',
        extra_context = {
            'examples': all_images[:28],
            'review_form': ReviewedItemForm(instance = ReviewedItem(content_type = ContentType.objects.get_for_model(Gear), content_object = gear)),
            'reviews': ReviewedItem.objects.filter(gear = gear),
            'content_type': ContentType.objects.get_for_model(Gear),
            'owners_count': UserProfile.objects.filter(**{user_attr_lookup[gear_type]: gear}).count(),
            'images_count': all_images.count(),
            'attributes': [
                (_(CLASS_LOOKUP[gear_type]._meta.get_field(k[0]).verbose_name),
                 getattr(gear, k[0]),
                 k[1]) for k in gear.attributes()],

            'show_tagline': show_commercial and gear.commercial.tagline,
            'show_link': show_commercial and gear.commercial.link,
            'show_image': show_commercial and gear.commercial.image,
            'show_other_images': show_commercial and gear.commercial.image and gear.commercial.image.revisions.all(),
            'show_description': show_commercial and gear.commercial.description,
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


@login_required
def set_default_frontpage_section(request, section):
    profile = request.user.userprofile
    profile.default_frontpage_section = section
    profile.save()

    messages.success(request, _("Default front page section changed."))
    return HttpResponseRedirect(reverse('index'))

