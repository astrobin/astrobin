from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import Http404
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list
from django.views.generic.list_detail import object_detail
from django.views.generic.create_update import create_object
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse
from django.core.exceptions import MultipleObjectsReturned, ValidationError
from django.conf import settings
from django.template import RequestContext
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import IntegrityError
from django.utils.translation import ugettext as _
from django.forms.models import formset_factory, inlineformset_factory
from django.utils.functional import curry
from django.utils.encoding import smart_str, smart_unicode

from haystack.query import SearchQuerySet, SQ
import persistent_messages

from uuid import uuid4
import os
import simplejson
import csv
import flickrapi
import urllib2
from datetime import datetime

from models import *
from forms import *
from management import NOTICE_TYPES
from notifications import *
from notification.models import NoticeSetting, NOTICE_MEDIA_DEFAULTS
from shortcuts import *
from tasks import *
from search_indexes import xapian_escape

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


def get_correct_gear(id):
    types = (
        Telescope,
        Mount,
        Camera,
        FocalReducer,
        Software,
        Filter,
        Accessory,
    )
    gear = None
    gear_type = None
    for type in types:
        try:
            gear = type.objects.get(id = id)
            gear_type = gear.__class__.__name__
            return (gear, gear_type)
        except type.DoesNotExist:
            continue

    return (None, None)


def is_gear_complete(id):
    gear, gear_type = get_correct_gear(id)
    
    ret = False
    if gear_type == 'Telescope':
        ret = (gear.aperture != None and
               gear.focal_length != None and
               gear.type != None)
    elif gear_type == 'Mount':
        ret = (gear.max_payload != None and
               gear.pe != None)
    elif gear_type == 'Camera':
        ret = (gear.pixel_size != None and
               gear.sensor_width != None and
               gear.sensor_height != None and
               gear.type != None)
    elif gear_type == 'FocalReducer':
        ret = True
    elif gear_type == 'Software':
        ret = (gear.type != None)
    elif gear_type == 'Filter':
        ret = (gear.type != None and
               gear.bandwidth != None)
    elif gear_type == 'Accessory':
        ret = True

    ret = ret and (gear.make != None) and (gear.make != '')
    return ret


def jsonDump(all):
    if len(all) > 0:
        return simplejson.dumps([{'id': i.id, 'name': i.name, 'complete': is_gear_complete(i.id)} for i in all])
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
    form = None

    profile = None
    if request.user.is_authenticated():
        profile = UserProfile.objects.get(user=request.user)
        if profile and profile.telescopes.all() and profile.cameras.all():
            form = ImageUploadForm()

    sqs = SearchQuerySet().all().models(Image).order_by('-uploaded')

    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
        'upload_form': form,
    }

    if 'upload_error' in request.GET:
        response_dict['upload_error'] = True

    return object_list(
        request, 
        queryset=sqs,
        template_name='index.html',
        template_object_name='image',
        paginate_by = 20,
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
    elif request.GET.get('sort') == '-integration':
        response_dict['sort'] = '-integration'
        sqs = sqs.order_by('-integration')
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

    return object_list(
        request, 
        queryset=sqs,
        template_name='wall.html',
        template_object_name='image',
        paginate_by = 100,
        extra_context = response_dict)


@require_GET
def messier(request):
    """Messier marathon"""

    queryset = MessierMarathon.objects.all().order_by('messier_number')
    response_dict = {
        'thumbnail_size': settings.THUMBNAIL_SIZE,
        's3_url': settings.S3_URL,
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
def image_detail(request, id):
    """ Show details of an image"""
    image = get_object_or_404(Image, pk=id)

    is_revision = False
    revision_id = 0
    revision_image = None
    revisions = ImageRevision.objects.filter(image=image)
    is_final = image.is_final
    is_ready = image.is_stored
    if 'r' in request.GET and request.GET.get('r') != '0':
        is_revision = True
        try:
            revision_id = int(request.GET['r'])
        except ValueError:
            from django.http import Http404
            raise Http404
        revision_image = get_object_or_404(ImageRevision, id=revision_id)
        is_final = revision_image.is_final
        revisions = revisions.exclude(id=revision_id)
        is_ready = revision_image.is_stored
    elif 'r' not in request.GET:
        if not is_final:
            final_revs = revisions.filter(is_final = True)
            # We should only have one
            if final_revs:
                final = revisions.filter(is_final = True)[0]
                return HttpResponseRedirect('/%i/?r=%i' % (image.id, final.id))

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
        telescopes = [xapian_escape(t.name) for t in image.imaging_telescopes.all()]
        related_images = related_images.filter(SQ(imaging_telescopes__in=telescopes))
    elif related == 'rel_imaging_camera':
        cameras = [xapian_escape(c.name) for c in image.imaging_cameras.all()]
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
            'frames': [],
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
                f = ""
                if a.filter:
                    f = "%s " % a.filter.name
                    if a.is_synthetic:
                        f += "(S) "
                f += '%sx%s"' % (a.number, a.duration)
                if a.iso:
                    f += ' @ ISO%s' % a.iso 
                if a.sensor_cooling:
                    f += ' @ %s\'C' % a.sensor_cooling
                if a.binning:
                    f+= ' bin %dx%d' % (a.binning, a.binning)

                dsa_data['frames'].append(f)
                dsa_data['integration'] += (a.duration * a.number / 3600.0)
                print dsa_data['integration']

            for i in ['darks', 'flats', 'flat_darks', 'bias']:
                if a.filter and getattr(a, i):
                    dsa_data[i].append("%s: %s" % (a.filter.name, getattr(a, i)))
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

        deep_sky_data = (
            (_('Resolution'), '%dx%d' % (image.w, image.h) if (image.w and image.h) else None),
            (_('Dates'), dsa_data['dates']),
            (_('Locations'), u', '.join([x.name for x in image.locations.all()])),
            (_('Frames'), ('\n' if len(dsa_data['frames']) > 1 else '') + u'\n'.join(dsa_data['frames'])),
            (_('Integration'), "%.1f %s" % (dsa_data['integration'], _("hours"))),
            (_('Darks') , ('\n' if len(dsa_data['darks']) > 1 else '') + u'\n'.join([smart_unicode(x) for x in dsa_data['darks']])),
            (_('Flats'), ('\n' if len(dsa_data['flats']) > 1 else '') + u'\n'.join([smart_unicode(x) for x in dsa_data['flats']])),
            (_('Flat darks'), ('\n' if len(dsa_data['flat_darks']) > 1 else '') + u'\n'.join([smart_unicode(x) for x in dsa_data['flat_darks']])),
            (_('Bias'), ('\n' if len(dsa_data['bias']) > 1 else '') + u'\n'.join([smart_unicode(x) for x in dsa_data['bias']])),
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
                     'small_thumbnail_size': settings.SMALL_THUMBNAIL_SIZE,
                     'resized_size': resized_size,
                     'already_voted': already_voted,
                     'current_rating': "%.2f" % rating,
                     'votes_number': votes,
                     'related': related,
                     'related_images': related_images,
                     'gear_list': gear_list,
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
                     'already_favorited': image in profile.favorites.all(),
                    }

    if 'upload_error' in request.GET:
        response_dict['upload_error'] = True

    return object_detail(
        request,
        queryset = Image.objects.all(),
        object_id = id,
        template_name = 'image/detail.html',
        template_object_name = 'image',
        extra_context = response_dict)


@require_GET
def image_full(request, id):
    image = get_object_or_404(Image, pk=id)

    is_revision = False
    revision_id = 0
    revision_image = None
    if 'r' in request.GET and request.GET.get('r') != '0':
            is_revision = True
            revision_id = int(request.GET['r'])
            revision_image = get_object_or_404(ImageRevision, id=revision_id)
            

    return object_detail(
        request,
        queryset = Image.objects.all(),
        object_id = id,
        template_name = 'image/full.html',
        template_object_name = 'image',
        extra_context = {
            's3_url': settings.S3_URL,
            'revision_image': revision_image,
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

    return render_to_response(
        "image_upload.html",
        {"form":ImageUploadForm()},
        context_instance=RequestContext(request))


@login_required
@require_POST
def image_upload_process(request):
    """Process the form"""
    if 'file' not in request.FILES:
        return HttpResponseRedirect('/?upload_error')

    form = ImageUploadForm(request.POST, request.FILES)
    file = request.FILES["file"]
    filename, original_ext = str(uuid4()), os.path.splitext(file.name)[1]
    original_ext = original_ext.lower()
    if original_ext == '.jpeg':
        original_ext = '.jpg'
    if original_ext not in ('.jpg', '.png', '.gif'):
        return HttpResponseRedirect('/?upload_error')

    try:
        from PIL import Image as PILImage
        trial_image = PILImage.open(file)
        trial_image.verify()
    except:
        return HttpResponseRedirect('/?upload_error')

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
@require_GET
def image_edit_presolve(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    form = ImageEditPresolveForm(instance=image)
    return render_to_response('image/edit/presolve.html',
        {'image': image,
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
    profile = UserProfile.objects.get(user=request.user)
    image = Image.objects.get(pk=id)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    no_gear = True
    if profile.telescopes and profile.cameras:
        no_gear = False

    form = ImageEditGearForm(user=request.user, instance=image)
    response_dict = {
        'form': form,
        's3_url':settings.S3_URL,
        'is_ready':image.is_stored,
        'image':image,
        'no_gear':no_gear,
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

    return HttpResponseRedirect('/%i/?r=%i' % (r.image.id, r.id))


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
def image_edit_save_presolve(request):
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)
    form = ImageEditPresolveForm(data=request.POST, instance=image)
    if request.user != image.user and not request.user.is_superuser:
        return HttpResponseForbidden()

    if not form.is_valid():
        return render_to_response("image/edit/presolve.html",
            {'image': image,
             'form': form,
            },
            context_instance = RequestContext(request))

    form.save()

    if image.is_stored:
        image.solve()

    done_later = 'done_later' in request.POST
    if done_later:
        if image.presolve_information > 1:
            return HttpResponseRedirect('/%s/?plate_solving_started' % image_id);
        else:
            return HttpResponseRedirect('/%s/' % image_id);

    return HttpResponseRedirect('/edit/watermark/%s/' % image_id)


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
        if 'submit_next' in request.POST:
            return HttpResponseRedirect('/edit/gear/%i/' % image.id)

        image.process(image.presolve_information > 1)
        return HttpResponseRedirect(image.get_absolute_url())

    return HttpResponseRedirect('/edit/basic/%i/?saved' % image.id)


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
    profile = UserProfile.objects.get(user = request.user)
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)
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
                             user=request.user,
                             instance=image)
    response_dict = {
        'image': image,
        's3_url':settings.S3_URL,
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

    return HttpResponseRedirect('/edit/gear/%i/?saved' % image.id)


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
        'is_ready':image.is_stored,
    }

    dsa_qs = DeepSky_Acquisition.objects.filter(image=image)
    solar_system_acquisition = None

    context_message = None

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
                        response_dict['context_message'] = {'error': False, 'text': _("Fill in one session, before adding more.")}
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

    return HttpResponseRedirect("/edit/acquisition/%s/?saved" % image_id)


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

    return HttpResponseRedirect('/edit/license/%s/?saved' % image_id)

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
    max_items = 16
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
                    ).distinct()[:max_items]:
                        k_dict[str(y)]['images'].append(i)

                l = _("No date specified")
                k_dict = {l: {'message': None, 'images': []}}
                k_dict[l]['message'] = _("To fill in the missing dates, use the <strong>Edit acquisition details</strong> entry in the <strong>Actions</strong> menu for each image.")
                k_list.append(k_dict)
                for i in sqs.filter(Q(acquisition = None) | Q(acquisition__date = None)).distinct():
                    k_dict[l]['images'].append(i)
               
                sqs = Image.objects.none()
        elif subsection == 'gear':
            if 'gear' in request.GET:
                gear = request.GET.get('gear')
                sqs = sqs.filter(Q(imaging_telescopes__name = gear) | Q(imaging_cameras__name = gear))
                subtitle = gear
                backlink = "?public&sub=gear"
            else:
                k_list = []
                smart_albums.append(k_list)
                for qs, filter in {
                    profile.telescopes.all(): 'imaging_telescopes',
                    profile.cameras.all(): 'imaging_cameras',
                }.iteritems():
                    for k in qs:
                        k_dict = {k.name: {'message': None, 'images': []}}
                        k_list.append(k_dict)
                        for i in sqs.filter(**{filter: k}).distinct()[:max_items]:
                            k_dict[k.name]['images'].append(i)

                l = _("No imaging telescopes or lenses, or no imaging cameras specified")
                k_dict = {l: {'message': None, 'images': []}}
                k_dict[l]['message'] = _("To fill in the missing gear, use the <strong>Edit gear used</strong> entry in the <strong>Actions</strong> menu for each image.")
                k_list.append(k_dict)
                for i in sqs.filter(Q(imaging_telescopes = None) | Q(imaging_cameras = None)).distinct():
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
                    for i in sqs.filter(Q(subjects__otype__in = r)).distinct()[:max_items]:
                        k_dict[l]['images'].append(i)

                l = _("Solar system")
                k_dict = {l: {'message': None, 'images': []}}
                k_list.append(k_dict)
                for i in sqs.filter(solar_system_main_subject__gte = 1):
                    k_dict[l]['images'].append(i)

                l = _("No subjects specified")
                k_dict = {l: {'message': None, 'images': []}}
                k_dict[l]['message'] = _("To fill in the missing subjects, use the <strong>Edit basic information</strong> entry in the <strong>Actions</strong> menu for each image.")
                k_list.append(k_dict)
                for i in sqs.filter(Q(subjects = None) & (Q(solar_system_main_subject = 0) | Q(solar_system_main_subject = None))).distinct():
                    k_dict[l]['images'].append(i)

                sqs = Image.objects.none()
        elif subsection == 'nodata':
            k_list = []
            smart_albums.append(k_list)

            l = _("No subjects specified")
            k_dict = {l: {'message': None, 'images': []}}
            k_dict[l]['message'] = _("To fill in the missing subjects, use the <strong>Edit basic information</strong> entry in the <strong>Actions</strong> menu for each image.")
            k_list.append(k_dict)
            for i in sqs.filter(Q(subjects = None) & (Q(solar_system_main_subject = 0) | Q(solar_system_main_subject = None))):
                k_dict[l]['images'].append(i)

            l = _("No imaging telescopes or lenses, or no imaging cameras specified")
            k_dict = {l: {'message': None, 'images': []}}
            k_list.append(k_dict)
            k_dict[l]['message'] = _("To fill in the missing gear, use the <strong>Edit gear used</strong> entry in the <strong>Actions</strong> menu for each image.")
            for i in sqs.filter(Q(imaging_telescopes = None) | Q(imaging_cameras = None)):
                k_dict[l]['images'].append(i)

            l = _("No acquisition details specified")
            k_dict = {l: {'message': None, 'images': []}}
            k_list.append(k_dict)
            k_dict[l]['message'] = _("To fill in the missing acquisition details, use the <strong>Edit acquisition details</strong> entry in the <strong>Actions</strong> menu for each image.")
            for i in sqs.filter(Q(acquisition = None)):
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
def user_page_favorites(request, username):
    user = get_object_or_404(User, username = username)
    profile  = UserProfile.objects.get(user = user)

    return object_list(
        request,
        queryset = profile.favorites.all(),
        template_name = 'user/favorites.html',
        template_object_name = 'image',
        paginate_by = 20,
        extra_context = {
            'thumbnail_size': settings.THUMBNAIL_SIZE,
             's3_url': settings.S3_URL,
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

    return HttpResponseRedirect("/profile/edit/basic/?saved");


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

    return HttpResponseRedirect('/profile/edit/license/?saved')


@login_required
@require_GET
def user_profile_edit_gear(request):
    """Edits own profile"""
    profile = UserProfile.objects.get(user=request.user)

    form = UserProfileEditGearForm()
    response_dict = {
        "form": form,
        'initial': 'initial' in request.GET,
    }
    prefill_dict = {}
    for attr in ["telescopes", "mounts", "cameras", "focal_reducers",
                 "software", "filters", "accessories"]:
        allGear = getattr(profile, attr).all()
        prefill_dict[attr] = jsonDump(allGear)
        form.fields[attr].initial = u', '.join(x.name for x in getattr(profile, attr).all())

    response_dict['prefill_dict'] = prefill_dict
    return render_to_response("user/profile/edit/gear.html",
                              response_dict,
                              context_instance=RequestContext(request))


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
    return HttpResponseRedirect('/profile/edit/locations/?saved');


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
                automerge = GearAutoMerge.objects.filter(label = gear_item.name)
                if automerge:
                    gear_item = v[0].objects.get(gear_ptr__pk = automerge[0].master.pk)
            except ValueError:
                automerge = GearAutoMerge.objects.filter(label = name)
                if automerge:
                    gear_item = v[0].objects.get(gear_ptr__pk = automerge[0].master.pk)
                else:
                    gear_item, created = v[0].objects.get_or_create(name = name)
            getattr(profile, k).add(gear_item)
        form.fields[k].initial = value

    profile.save()

    initial = "&initial=true" if "initial" in request.POST else ""
    return HttpResponseRedirect("/profile/edit/gear/?saved" + initial);


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

    return HttpResponseRedirect("/profile/edit/preferences/?saved");


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
    file = None
    image_id = request.POST['image_id']
    image = Image.objects.get(id=image_id)

    form = ImageRevisionUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseRedirect('/%i/?upload_error' % image.id)
    file = request.FILES["file"]

    filename, original_ext = str(uuid4()), os.path.splitext(file.name)[1]
    original_ext = original_ext.lower()
    if original_ext == '.jpeg':
        original_ext = '.jpg'
    if original_ext not in ('.jpg', '.png', '.gif'):
        return HttpResponseRedirect('/%i/?upload_error' % image.id)

    try:
        from PIL import Image as PILImage
        trial_image = PILImage.open(file)
        trial_image.verify()
    except:
        return HttpResponseRedirect('/%i/?upload_error' % image.id)

    destination = open(settings.UPLOADS_DIRECTORY + filename + original_ext, 'wb+')
    for chunk in file.chunks():
        destination.write(chunk)
    destination.close()

    revisions = ImageRevision.objects.filter(image = image)
    for r in revisions:
        r.is_final = False
        r.save()

    image.is_final = False
    image.save()

    image_revision = ImageRevision(image=image, filename=filename, original_ext=original_ext, is_final=True)
    image_revision.save()
    image_revision.process()

    return HttpResponseRedirect(image_revision.get_absolute_url())


@login_required
@require_GET
def stats(request):
    response_dict = {}

    sqs = SearchQuerySet()

    response_dict['total_users'] = sqs.models(User).filter(user_images__gt = 0).count()
    response_dict['total_images'] = sqs.models(Image).all().count()
    hours = 0
    for i in sqs.filter().models(Image):
        hours += i.integration
    response_dict['total_integration'] = int(hours / 3600.0)

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
def help(request):
    return render_to_response('help.html',
        context_instance=RequestContext(request))


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

    response_dict = {
        'form': form.as_p() if form else '',
    }

    return HttpResponse(
        simplejson.dumps(response_dict),
        mimetype = 'application/javascript')


@require_POST
@login_required
def save_gear_details(request):
    id = request.POST.get('gear_id')
    gear, gear_type = get_correct_gear(id)

    form = None
    if gear_type == 'Telescope':
        form = TelescopeEditForm(data = request.POST, instance = gear)
    elif gear_type == 'Mount':
        form = MountEditForm(data = request.POST, instance = gear)
    elif gear_type == 'Camera':
        form = CameraEditForm(data = request.POST, instance = gear)
    elif gear_type == 'FocalReducer':
        form = FocalReducerEditForm(data = request.POST, instance = gear)
    elif gear_type == 'Software':
        form = SoftwareEditForm(data = request.POST, instance = gear)
    elif gear_type == 'Filter':
        form = FilterEditForm(data = request.POST, instance = gear)
    elif gear_type == 'Accessory':
        form = AccessoryEditForm(data = request.POST, instance = gear)

    if not form or not form.is_valid():
        response_dict = {
            'form': form.as_p() if form else '',
        }
        return HttpResponse(
            simplejson.dumps(response_dict),
            mimetype = 'application/javascript')

    form.save()
    return ajax_success()


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
def favorite_ajax(request, id):
    profile = UserProfile.objects.get(user = request.user)
    image = get_object_or_404(Image, pk=id)

    if image in profile.favorites.all():
        return HttpResponseForbidden()

    profile.favorites.add(image)
    profile.save()

    if image.user != request.user:
        push_notification(
            [image.user], 'new_favorite',
            {
                'url': settings.ASTROBIN_BASE_URL + image.get_absolute_url(),
                'user': request.user,
            }
        )

    return ajax_success();

