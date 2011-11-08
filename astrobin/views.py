from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list
from django.views.generic.list_detail import object_detail
from django.views.generic.create_update import create_object
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
from django.forms.models import inlineformset_factory
from django.utils.functional import curry

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
from notifications import *
from shortcuts import *
from tasks import *
from search_indexes import xapian_escape

def valueReader(request, field):
    def utf_8_encoder(data):
        for line in data:
            yield line.encode('utf-8')

    as_field = 'as_values_' + field
    if as_field in request.POST:
        value = request.POST[as_field]
    elif field in request.POST:
        value = request.POST[field]
    else:
        return [], ""

    items = []
    reader = csv.reader(utf_8_encoder([value]),
                        skipinitialspace = True)
    for row in reader:
        items += [unicode(x, 'utf-8') for x in row if x != '']

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
        return simplejson.dumps([{'id': i.id, 'name': i.name} for i in all])
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

    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        pass

    if profile and profile.telescopes.all() and profile.cameras.all():
        form = ImageUploadForm()
    return object_list(
        request, 
        queryset=Image.objects.filter(is_stored=True),
        template_name='index.html',
        template_object_name='image',
        extra_context = {'thumbnail_size':settings.THUMBNAIL_SIZE,
                         's3_url':settings.S3_URL,
                         'upload_form':form,})


@require_GET
def no_javascript(request):
    return render_to_response('no_javascript.html',
        context_instance=RequestContext(request))


@require_GET
def image_detail(request, id):
    """ Show details of an image"""
    from moon import MoonPhase;

    image = get_object_or_404(Image, pk=id)
    is_ready = image.is_stored

    already_voted = bool(image.rating.get_rating_for_user(request.user, request.META['REMOTE_ADDR']))
    votes = image.rating.votes
    score = image.rating.score
    rating = float(score)/votes if votes > 0 else 0

    limit = 10
    related = None
    related_images = None
    if 'related' in request.GET:
        related = request.GET['related']
    else:
        related = 'user'

    if related == 'user':
        related_images = SearchQuerySet().filter(user=image.user.username).exclude(django_id=id).order_by('-uploaded')[:limit]
    elif related == 'subject':
        subjects = [xapian_escape(s.mainId) for s in image.subjects.all()]
        related_images = SearchQuerySet().filter(SQ(subjects__in=subjects)).exclude(django_id=id).order_by('-uploaded')[:limit]
    elif related == 'imaging_telescope':
        telescopes = [xapian_escape(t.name) for t in image.imaging_telescopes.all()]
        related_images = SearchQuerySet().filter(SQ(imaging_telescopes__in=telescopes)).exclude(django_id=id).order_by('-uploaded')[:limit]
    elif related == 'imaging_camera':
        cameras = [xapian_escape(c.name) for c in image.imaging_cameras.all()]
        related_images = SearchQuerySet().filter(SQ(imaging_cameras__in=cameras)).exclude(django_id=id).order_by('-uploaded')[:limit]

    gear_list = [('Imaging telescopes', image.imaging_telescopes.all()),
                 ('Imaging cameras'   , image.imaging_cameras.all()),
                 ('Mounts'            , image.mounts.all()),
                 ('Guiding telescopes', image.guiding_telescopes.all()),
                 ('Guiding cameras'   , image.guiding_cameras.all()),
                 ('Focal reducers'    , image.focal_reducers.all()),
                 ('Software'          , image.software.all()),
                 ('Filters'           , image.filters.all()),
                 ('Accessories'       , image.accessories.all()),
                ]

    deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=image)
    solar_system_acquisition = None
    image_type = None
    deep_sky_data = {}

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=image)
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
            'darks': [],
            'flats': [],
            'flat_darks': [],
            'bias': [],
            'mean_sqm': [],
            'mean_fwhm': [],
        }
        for a in deep_sky_acquisitions:
            if a.date is not None:
                dsa_data['dates'].append(a.date)
                m = MoonPhase(a.date)
                moon_age_list.append(m.age)
                moon_illuminated_list.append(m.illuminated)

            if a.number and a.duration:
                f = ""
                if a.filter:
                    f = a.filter.name
                    if a.is_synthetic:
                        f += " (S)"
                f += '%sx%s"' % (a.number, a.duration)
                if a.iso:
                    f += ' @ ISO%s' % a.iso 
                if a.sensor_cooling:
                    f += ' @ %s\'C' % a.sensor_cooling

                dsa_data['frames'].append(f)

            for i in ['darks', 'flats', 'flat_darks', 'bias']:
                if a.filter and getattr(a, i):
                    dsa_data[i].append("%s: %s" % (a.filter.name, getattr(a, i)))
                elif getattr(a, i):
                    dsa_data[i].append(getattr(a, i))

            if a.mean_sqm:
                dsa_data['mean_sqm'].append(a.mean_sqm)

            if a.mean_fwhm:
                dsa_data['mean_fwhm'].append(a.mean_fwhm)

        def average(values):
            if not len(values):
                return 0
            return float(sum(values)) / len(values)

        deep_sky_data = {
            _('Dates'): u', '.join([str(x) for x in dsa_data['dates']]),
            _('Frames'): u', '.join(dsa_data['frames']),
            _('Darks') : u', '.join([str(x) for x in dsa_data['darks']]),
            _('Flats'): u', '.join([str(x) for x in dsa_data['flats']]),
            _('Flat darks'): u', '.join([str(x) for x in dsa_data['flat_darks']]),
            _('Bias'): u', '.join([str(x) for x in dsa_data['bias']]),
            _('Avg. Moon age'): "%.2f" % (average(moon_age_list), ) if moon_age_list else None,
            _('Avg. Moon phase'): "%.2f" % (average(moon_illuminated_list), ) if moon_illuminated_list else None,
            _('Mean SQM'): "%.2f" % (average([float(x) for x in dsa_data['mean_sqm']])) if dsa_data['mean_sqm'] else None,
            _('Mean FWHM'): "%.2f" % (average([float(x) for x in dsa_data['mean_fwhm']])) if dsa_data['mean_fwhm'] else None,
        }

    elif solar_system_acquisition:
        image_type = 'solar_system'

    follows = False
    if request.user.is_authenticated():
        profile = UserProfile.objects.get(user=request.user)
        if UserProfile.objects.get(user=image.user) in profile.follows.all():
            follows = True

    is_revision = False
    revision_id = 0
    revision_image = None
    revisions = ImageRevision.objects.filter(image=image)
    if 'r' in request.GET:
        is_revision = True
        revision_id = int(request.GET['r'])
        revision_image = ImageRevision.objects.get(id=revision_id)
        revisions = revisions.exclude(id=revision_id)
        is_ready = revision_image.is_stored

    return object_detail(
        request,
        queryset = Image.objects.all(),
        object_id = id,
        template_name = 'image/detail.html',
        template_object_name = 'image',
        extra_context = {'s3_url': settings.S3_URL,
                         'already_voted': already_voted,
                         'current_rating': rating,
                         'related': related,
                         'related_images': related_images,
                         'gear_list': gear_list,
                         'image_type': image_type,
                         'deep_sky_data': deep_sky_data,
                         'inverted': True if 'mod' in request.GET and request.GET['mod'] == 'inverted' else False,
                         'solved': True if 'mod' in request.GET and request.GET['mod'] == 'solved' else False,
                         'follows': follows,
                         'private_message_form': PrivateMessageForm(),
                         'bring_to_attention_form': BringToAttentionForm(),
                         'upload_revision_form': ImageRevisionUploadForm(),
                         'revisions': revisions,
                         'is_revision': is_revision,
                         'revision_image': revision_image,
                         'is_ready': is_ready,
                         'full': 'full' in request.GET,
                        })


@require_GET
def image_get_rating(request, image_id):
    image = get_object_or_404(Image, pk=image_id)
    votes = image.rating.votes
    score = image.rating.score
    rating = float(score)/votes if votes > 0 else 0

    response_dict = {'rating': rating}
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

    form = ImageUploadForm(request.POST, request.FILES)
    file = request.FILES["file"]
    try:
        from PIL import Image as PILImage
        trial_image = PILImage.open(file)
        trial_image.verify()
    except:
        return object_list(
            request,
            queryset=Image.objects.filter(is_stored=True)[:15],
            template_name='index.html',
            template_object_name='image',
            extra_context = {'thumbnail_size':settings.THUMBNAIL_SIZE,
                             's3_url':settings.S3_URL,
                             'upload_form': ImageUploadForm(),
                             'context_message': {'error': True, 'text': _("Invalid image.")}})

    filename, original_ext = str(uuid4()), os.path.splitext(file.name)[1]
    destination = open(settings.UPLOADS_DIRECTORY + filename + original_ext, 'wb+')
    for chunk in file.chunks():
        destination.write(chunk)
    destination.close()
    image = Image(
        filename=filename,
        original_ext=original_ext,
        user=request.user)

    image.save()
    image.process()

    followers = [x.from_userprofile.user
                 for x in UserProfile.follows.through.objects.filter(to_userprofile=request.user)]
    push_notification(followers, 'new_image',
                      {'originator':request.user,
                       'object_url':image.get_absolute_url()})

    return render_to_response('image/edit/basic.html',
        {'image':image,
         's3_url':settings.S3_URL,
         'form':ImageEditBasicForm(),
         'prefill_dict': {
            'subjects': ['[]',
                         _("Enter partial name and wait for the suggestions!"),
                         _("No results. Sorry.")],
            'locations': ['[]',
                          _("Enter partial name and wait for the suggestions!"),
                          _("No results. Press TAB to create this location!")],
         },
         'is_ready':image.is_stored,
        },
        context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_basic(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user:
        return HttpResponseForbidden()

    subjects =  u', '.join(x.mainId for x in image.subjects.all())
    locations = u', '.join(x.name for x in image.locations.all())

    form = ImageEditBasicForm(data={
        'title': image.title,
        'description': image.description,
        'subjects': subjects,
        'locations': locations,
    })

    return render_to_response('image/edit/basic.html',
        {'image':image,
         's3_url':settings.S3_URL,
         'form':form,
         'prefill_dict': {
            'subjects': [jsonDumpSubjects(image.subjects.all()),
                         _("Enter partial name and wait for the suggestions!"),
                         _("No results. Sorry."),
                         _("Subjects found in the SIMBAD database")],
            'locations': [jsonDump(image.locations.all()),
                          _("Enter partial name and wait for the suggestions!"),
                          _("No results. Press TAB to create this location!"),
                          _("Matching items (press TAB to add what you typed instead):")],
         },
         'is_ready': image.is_stored,
         'subjects': subjects,
         'locations': locations,
        },
        context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_gear(request, id):
    profile = UserProfile.objects.get(user=request.user)
    image = Image.objects.get(pk=id)
    if request.user != image.user:
        return HttpResponseForbidden()

    form = ImageEditGearForm(user=request.user, instance=image)
    response_dict = {
        'form': form,
        's3_url':settings.S3_URL,
        'is_ready':image.is_stored,
        'image':image,
    }

    return render_to_response('image/edit/gear.html',
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_acquisition(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user:
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
    if edit_type == 'deep_sky':
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

    response_dict = {
        'image': image,
        'edit_type': edit_type,
        'deep_sky_acquisitions': deep_sky_acquisition_formset,
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
    if request.user != image.user:
        return HttpResponseForbidden()

    DeepSky_Acquisition.objects.filter(image=image).delete()
    SolarSystem_Acquisition.objects.filter(image=image).delete()

    response_dict = {
        'image': image,
        's3_url':settings.S3_URL,
        'is_ready':image.is_stored,
    }
    return render_to_response('image/edit/acquisition.html',
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_POST
def image_edit_save_basic(request):
    form = ImageEditBasicForm(data=request.POST)
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)
    if request.user != image.user:
        return HttpResponseForbidden()

    subjects =  u', '.join(x.mainId for x in image.subjects.all())
    locations = u', '.join(x.name for x in image.locations.all())

    response_dict = {
        'image': image,
        's3_url': settings.S3_URL,
        'form': form,
        'prefill_dict': {
           'subjects': [jsonDumpSubjects(image.subjects.all()),
                        _("Enter partial name and wait for the suggestions!"),
                        _("No results. Sorry.")],
           'locations': [jsonDump(image.locations.all()),
                         _("Enter partial name and wait for the suggestions!"),
                         _("No results. Press TAB to create this location!")],
        },
        'is_ready': image.is_stored,
        'subjects': subjects,
        'locations': locations,
    }

    if not form.is_valid():
        return render_to_response("image/edit/basic.html",
            response_dict,
            context_instance=RequestContext(request))

    prefill_dict = {}

    image.subjects.clear()
    image.locations.clear()

    (ids, value) = valueReader(request, 'subjects')
    if ids:
        for id in ids:
            k = None
            try:
                k = Subject.objects.get(Q(id=id))
            except (Subject.DoesNotExist, ValueError):
                '''User pressed TAB without waiting for autocomplete,
                or on something that didn't find a match in Simbad.
                Let's try to match it once more, in case it indeed
                was a case of premature TAB.'''
                import simbad
                subjects = simbad.find_subjects(id.strip())
                if subjects:
                    k = subjects[0]
            image.subjects.add(k)
    prefill_dict['subjects'] = [jsonDumpSubjects(image.subjects.all()),
                                _("Enter partial name and wait for the suggestions!"),
                                _("No results. Sorry.")]

    form.fields['subjects'].initial = u', '.join(x.mainId for x in getattr(image, 'subjects').all())

    (ids, value) = valueReader(request, 'locations')
    if ids:
        for id in ids:
            try:
                try:
                    id = float(id)
                    k = Location.objects.get(Q(id=id))
                except ValueError:
                    k = Location.objects.get(Q(name=id))
            except (Location.DoesNotExist, ValueError):
                k = Location(name=id)
                k.save();

                r = LocationRequest(
                    from_user=User.objects.get(username=settings.ASTROBIN_USER),
                    to_user=image.user,
                    location=k,
                    fulfilled=False,
                    message='') # not implemented yet
                r.save()
                push_request(image.user, r)

            image.locations.add(k)
    prefill_dict['locations'] = [jsonDump(image.locations.all()),
                                 _("Enter partial name and wait for the suggestions!"),
                                 _("No results. Sorry.")]


    form.fields['locations'].initial = u', '.join(x.name for x in getattr(image, 'locations').all())

    image.title = form.cleaned_data['title'] 
    image.description = form.cleaned_data['description']

    image.save()

    response_dict['prefill_dict'] = prefill_dict
    return HttpResponseRedirect('/edit/basic/%i/?saved' % image.id)


@login_required
@require_POST
def image_edit_save_gear(request):
    profile = UserProfile.objects.get(user = request.user)
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)
    if request.user != image.user:
        return HttpResponseForbidden()

    image.imaging_telescopes.clear()
    image.guiding_telescopes.clear()
    image.mounts.clear()
    image.imaging_cameras.clear()
    image.guiding_cameras.clear()
    image.focal_reducers.clear()
    image.filters.clear()
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

    return HttpResponseRedirect('/edit/gear/%i/?saved' % image.id)


@login_required
@require_POST
def image_edit_save_acquisition(request):
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)
    if request.user != image.user:
        return HttpResponseForbidden()

    edit_type = request.POST.get('edit_type')
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

    if edit_type == 'deep_sky':
        DSAFormSet = inlineformset_factory(Image, DeepSky_Acquisition, can_delete=False, form=DeepSky_AcquisitionForm)
        deep_sky_acquisition_formset = DSAFormSet(request.POST, instance=image)
        response_dict['deep_sky_acquisitions'] = deep_sky_acquisition_formset
        if deep_sky_acquisition_formset.is_valid():
            deep_sky_acquisition_formset.save()
            if 'add_more' in request.POST:
                DSAFormSet = inlineformset_factory(Image, DeepSky_Acquisition, extra=1, can_delete=False, form=DeepSky_AcquisitionForm)
                deep_sky_acquisition_formset = DSAFormSet(instance=image)
                response_dict['deep_sky_acquisitions'] = deep_sky_acquisition_formset
                if not dsa_qs:
                    response_dict['context_message'] = {'error': False, 'text': _("Fill in one session, before adding more.")}
                return render_to_response('image/edit/acquisition.html',
                    response_dict,
                    context_instance=RequestContext(request))
        else:
            response_dict['context_message'] = {'error': True, 'text': _("There was an error. Check your input!")}
            return render_to_response('image/edit/acquisition.html',
                                      response_dict,
                                      context_instance=RequestContext(request))

    elif edit_type == 'solar_system':
        date = request.POST.get('date')
        if date == 'yyyy-mm-dd':
            date = None
        try:
            if date is not None:
                datetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            date = None

        time = request.POST.get('time')
        if time == 'hh:mm':
            time = None
        try:
            if time is not None:
                datetime.datetime.strptime(time, '%H:%M')
        except ValueError:
            time = None

        solar_system_acquisition = SolarSystem_Acquisition(
            image = image,
            date = date,
            time = time)
        for k in ['frames', 'fps', 'focal_length', 'cmi', 'cmii',
                  'cmiii', 'seeing', 'transparency']:
            v = request.POST.get(k)
            if v != '':
                setattr(solar_system_acquisition, k, v)

        try:
            solar_system_acquisition.save()
        except ValidationError:
            response_dict['context_message'] = {'error': True, 'text': _("There was an error. Check your input!")}
            response_dict['solar_system_acquisitions'] = solar_system_acquisition
            return render_to_response('image/edit/acquisition.html',
                                      response_dict,
                                      context_instance=RequestContext(request))

    return HttpResponseRedirect("/edit/acquisition/%s/?saved" % image_id)


@login_required
@require_GET
def image_delete(request, id):
    image = get_object_or_404(Image, pk=id) 
    if request.user != image.user:
        return HttpResponseForbidden()

    image.delete()
    push_notification([request.user], 'image_deleted', {});

    return HttpResponseRedirect("/");

@require_GET
def user_page(request, username):
    """Shows the user's public page"""
    user = User.objects.get(username=username)
    profile = UserProfile.objects.get(user=user)

    gear_list = [('Telescopes'    , profile.telescopes.all()),
                 ('Mounts'        , profile.mounts.all()),
                 ('Cameras'       , profile.cameras.all()),
                 ('Focal reducers', profile.focal_reducers.all()),
                 ('Software'      , profile.software.all()),
                 ('Filters'       , profile.filters.all()),
                 ('Accessories'   , profile.accessories.all()),
                ]

    return object_list(
        request,
        queryset=Image.objects.filter(user=user),
        template_name='user/profile.html',
        template_object_name='image',
        extra_context = {'thumbnail_size':settings.THUMBNAIL_SIZE,
                         's3_url':settings.S3_URL,
                         'user':user,
                         'gear_list':gear_list})


@login_required
@require_GET
def user_profile_edit_basic(request):
    """Edits own profile"""
    profile = UserProfile.objects.get(user = request.user)
    form = UserProfileEditBasicForm(instance = profile)
    form.fields['locations'].initial = u', '.join(x.name for x in profile.locations.all())
    response_dict = {
        'form': form,
        'prefill_dict': {'locations': jsonDump(profile.locations.all())}
    }
    return render_to_response("user/profile/edit/basic.html",
        response_dict,
        context_instance=RequestContext(request))


@login_required
@require_POST
def user_profile_save_basic(request):
    """Saves the form"""

    form = UserProfileEditBasicForm(data=request.POST)
    profile = UserProfile.objects.get(user = request.user)
    response_dict = {'form': form}

    if form.is_valid():
        profile.locations.clear()
        (ids, value) = valueReader(request, 'locations')
        for id in ids:
            k = None
            try:
                try:
                    id = float(id)
                    k = Location.objects.get(Q(id=id))
                except ValueError:
                    k = Location.objects.get(Q(name=id))
            except (Location.DoesNotExist, ValueError):
                k = Location(name=id)
                k.save();

                r = LocationRequest(
                    from_user=User.objects.get(username=settings.ASTROBIN_USER),
                    to_user=request.user,
                    location=k,
                    fulfilled=False,
                    message='') # not implemented yet
                r.save()
                push_request(request.user, r)

            profile.locations.add(k)

        profile.website  = form.cleaned_data['website']
        profile.job      = form.cleaned_data['job']
        profile.hobbies  = form.cleaned_data['hobbies']

        profile.save()
    else:
        response_dict['prefill_dict'] = {'locations': jsonDump(profile.locations.all()) }
        return render_to_response("user/profile/edit/basic.html",
            response_dict,
            context_instance=RequestContext(request))

    return HttpResponseRedirect("/profile/edit/basic/?saved");


@login_required
@require_GET
def user_profile_edit_gear(request):
    """Edits own profile"""
    profile = UserProfile.objects.get(user=request.user)

    form = UserProfileEditGearForm()
    response_dict = {"form": form}
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
@require_POST
def user_profile_save_gear(request):
    """Saves the form"""

    profile = UserProfile.objects.get(user = request.user)

    profile.telescopes.clear()
    profile.mounts.clear()
    profile.cameras.clear()
    profile.focal_reducers.clear()
    profile.filters.clear()
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
        (names, value) = valueReader(request, k)
        for name in names:
                    gear_item, created = v[0].objects.get_or_create(name = name)
                    if created:
                        gear_item.save()
                    getattr(profile, k).add(gear_item)
        form.fields[k].initial = value

    profile.save()

    return HttpResponseRedirect("/profile/edit/gear/?saved");


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

                    image = Image(filename=filename, original_ext=original_ext,
                                  user=request.user,
                                  title=title if title is not None else '',
                                  description=description if description is not None else '')
                    image.save()
                    image.process()

                    followers = [x.from_userprofile.user
                                 for x in UserProfile.follows.through.objects.filter(to_userprofile=request.user)]
                    push_notification(followers, 'new_image',
                                      {'originator':request.user,
                                       'object_url':image.get_absolute_url()})

        return ajax_response(response_dict)

    return render_to_response("user/profile/flickr_import.html",
                              response_dict,
                              context_instance=RequestContext(request))


def flickr_auth_callback(request):
    f = flickrapi.FlickrAPI(settings.FLICKR_API_KEY,
                            settings.FLICKR_SECRET, store_token = False)

    frob = request.GET['frob']
    try:
        token = f.get_token(frob)
    except flickrapi.FlickrError:
        token = None
    request.session['flickr_token'] = token

    return HttpResponseRedirect("/profile/edit/flickr/")


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
        return HttpResponseRedirect(request.GET['next'])


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
        return HttpResponseRedirect(request.GET['next'])


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
def messages_new(request, username):
    form = PrivateMessageForm()
    return render_to_response('messages/new.html',
        {'form': form,
         'to_user': username},
        context_instance=RequestContext(request))


@login_required
@require_POST
def messages_save(request):
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

        return render_to_response('messages/sent.html',
            context_instance=RequestContext(request))


@login_required
@require_GET
def messages_all(request):
    return object_list(
        request,
        queryset=persistent_messages.models.Message.objects.filter(user=request.user),
        template_name='messages/all.html',
        template_object_name='message',
        extra_context={})


@login_required
@require_GET
def message_detail(request, id):
    subject = '%s: %s' % (_('RE'), persistent_messages.models.Message.objects.get(id=id).subject)
    return object_detail(
        request,
        queryset=persistent_messages.models.Message.objects.all(),
        object_id=id,
        template_name='messages/detail.html',
        template_object_name='message',
        extra_context={'private_message_form':PrivateMessageForm(initial={'subject':subject})})


@login_required
@require_POST
def bring_to_attention(request):
    form = BringToAttentionForm(data=request.POST)
    image_id = request.POST.get('image_id')
    try:
        image = Image.objects.get(id=image_id)
    except:
        return ajax_fail()

    if not form.is_valid():
        return ajax_fail()

    (usernames, value) = valueReader(request, 'user')
    recipients = []
    for username in usernames:
        user = User.objects.get(username=username)
        if user is not None:
            recipients.append(user)

    push_notification(recipients, 'attention_request',
                      {'object':image,
                       'object_url':settings.ASTROBIN_SHORT_BASE_URL + image.get_absolute_url(),
                       'originator':request.user,
                       'originator_url': request.user.get_absolute_url()})

    return ajax_success()


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
    image = None
    try:
        image = Image.objects.get(id=image_id)
    except:
        return ajax_fail()

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

    return ajax_success()


@login_required
@require_GET
def image_request_fits(request, image_id):
    image = None
    try:
        image = Image.objects.get(id=image_id)
    except:
        return ajax_fail()

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

    return ajax_success()


@login_required
@require_POST
def image_revision_upload_process(request):
    file = None
    image_id = request.POST['image_id']
    image = Image.objects.get(id=image_id)

    form = ImageRevisionUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseRedirect(image.get_absolute_url())
    file = request.FILES["file"]

    filename, original_ext = str(uuid4()), os.path.splitext(file.name)[1]
    destination = open(settings.UPLOADS_DIRECTORY + filename + original_ext, 'wb+')
    for chunk in file.chunks():
        destination.write(chunk)
        destination.close()

    image_revision = ImageRevision(image=image, filename=filename, original_ext=original_ext)
    image_revision.save()
    image_revision.process()

    followers = [x.from_userprofile.user
                 for x in UserProfile.follows.through.objects.filter(to_userprofile=request.user)]
    push_notification(followers, 'new_image_revision',
                      {'originator':request.user,
                       'object_url':settings.ASTROBIN_SHORT_BASE_URL + image_revision.get_absolute_url()})

    return HttpResponseRedirect(image_revision.get_absolute_url())


@require_GET
def help(request):
    return render_to_response('help.html',
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


@login_required
@require_POST
def location_save(request):
    id = request.POST.get('location_id')
    location = Location.objects.get(pk=id)
    form = LocationEditForm(data=request.POST, instance=location)
    if not form.is_valid():
        return render_to_response('location/edit.html',
            {'form': form,
             'id': id},
            context_instance=RequestContext(request))

    form.save()

    # Now let's mark the request as fullfilled, if it exists.
    try:
        req = LocationRequest.objects.get(
            from_user = request.user,
            location = id,
            fulfilled = False)
        req.fulfilled = True
        req.save()
    except:
        pass

    return render_to_response('location/edit.html',
        {'form' : form,
         'id'   : id,
         'saved': True,
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
