from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list
from django.views.generic.list_detail import object_detail
from django.views.generic.create_update import create_object
from django.core.urlresolvers import reverse
from django.conf import settings
from django.template import RequestContext
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from uuid import uuid4
import os
import simplejson
import csv
import flickrapi
import urllib

from models import *
from forms import *
from file_utils import *

def jsonDump(all):
    if len(all) > 0:
        return simplejson.dumps([{'value_unused': i.id, 'name': i.name} for i in all])
    else:
        return []


# VIEWS

def index(request):
    """Main page"""

    # get ABPOD
    try:
        abpod = ABPOD.objects.all()[0]
    except IndexError:
        abpod = None

    return object_list(
        request, 
        queryset=Image.objects.all()[:8],
        template_name='index.html',
        template_object_name='image',
        extra_context = {"thumbnail_size":settings.THUMBNAIL_SIZE,
                         "s3_thumbnails_bucket":settings.S3_THUMBNAILS_BUCKET,
                         "s3_abpod_bucket":settings.S3_ABPOD_BUCKET,
                         "s3_url":settings.S3_URL,
                         "upload_form": ImageUploadForm(),
                         "abpod":abpod})



@require_GET
def no_javascript(request):
    return render_to_response('no_javascript.html',
        context_instance=RequestContext(request))


def image_detail(request, id):
    """ Show details of an image"""
    image = get_object_or_404(Image, pk=id)
    already_voted = bool(image.rating.get_rating_for_user(request.user, request.META['REMOTE_ADDR']))
    votes = image.rating.votes
    score = image.rating.score
    rating = float(score)/votes if votes > 0 else 0

    user_images = Image.objects.filter(user=image.user).exclude(pk=id)[:10]

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
    deep_sky_data = [['Dates', None],
                     ['Light frames', None],
                     ['R frames', None],
                     ['G frames', None],
                     ['B frames', None],
                     ['Dark frames', None],
                     ['Offset/bias frames', None],
                     ['Flat frames', None],
                     ['Flat dark frames', None]
                    ]

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=image)
    except:
        pass

    if deep_sky_acquisitions:
        image_type = 'deep_sky'

        deep_sky_data[0][1] = [a.date for a in deep_sky_acquisitions if a.date is not None]
        deep_sky_data[1][1] = ['%dx%d @ ISO%d' % (a.number, a.duration, a.iso) for a in deep_sky_acquisitions if a.acquisition_type == 'l']
        deep_sky_data[2][1] = ['%dx%d @ ISO%d' % (a.number, a.duration, a.iso) for a in deep_sky_acquisitions if a.acquisition_type == 'r']
        deep_sky_data[3][1] = ['%dx%d @ ISO%d' % (a.number, a.duration, a.iso) for a in deep_sky_acquisitions if a.acquisition_type == 'g']
        deep_sky_data[4][1] = ['%dx%d @ ISO%d' % (a.number, a.duration, a.iso) for a in deep_sky_acquisitions if a.acquisition_type == 'b']
        deep_sky_data[5][1] = [a.number for a in deep_sky_acquisitions if a.acquisition_type == 'd']
        deep_sky_data[6][1] = [a.number for a in deep_sky_acquisitions if a.acquisition_type == 'o']
        deep_sky_data[7][1] = [a.number for a in deep_sky_acquisitions if a.acquisition_type == 'f']
        deep_sky_data[8][1] = [a.number for a in deep_sky_acquisitions if a.acquisition_type == 'x']
    elif solar_system_acquisition:
        image_type = 'solar_system'


    return object_detail(
        request,
        queryset = Image.objects.all(),
        object_id = id,
        template_name = 'image_detail.html',
        template_object_name = 'image',
        extra_context = {'s3_images_bucket': settings.S3_IMAGES_BUCKET,
                         's3_resized_images_bucket': settings.S3_RESIZED_IMAGES_BUCKET,
                         's3_thumbnails_bucket': settings.S3_THUMBNAILS_BUCKET,
                         's3_small_thumbnails_bucket': settings.S3_SMALL_THUMBNAILS_BUCKET,
                         's3_inverted_bucket': settings.S3_INVERTED_BUCKET,
                         's3_resized_inverted_bucket': settings.S3_RESIZED_INVERTED_BUCKET,
                         's3_histograms_bucket': settings.S3_HISTOGRAMS_BUCKET,
                         's3_url': settings.S3_URL,
                         'already_voted': already_voted,
                         'current_rating': rating,
                         'user_images': user_images,
                         'gear_list': gear_list,
                         'image_type': image_type,
                         'deep_sky_data': deep_sky_data,
                         'inverted': True if 'mod' in request.GET and request.GET['mod'] == 'inverted' else False})


@require_GET
def image_get_rating(request, image_id):
    image = get_object_or_404(Image, pk=image_id)
    votes = image.rating.votes
    score = image.rating.score
    rating = float(score)/votes if votes > 0 else 0

    response_dict = {'rating': rating}
    return HttpResponse(simplejson.dumps(response_dict),
                        mimetype='application/javascript')


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
    file = None
    if 'qqfile' in request.GET:
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile(request.GET['qqfile'], request.raw_post_data)
    else:
        form = ImageUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render_to_response("index.html", {"upload_form":form},
                context_instance=RequestContext(request))
        file = request.FILES["file"]

    s3_filename = str(uuid4()) + os.path.splitext(file.name)[1]
    store_image_in_s3(file, s3_filename)

    image = Image(filename = s3_filename, user = request.user)
    image.save()

    if 'qqfile' in request.GET:
        return_dict = {'success':'true', 'id':image.id}
        return HttpResponse(simplejson.dumps(return_dict),
                            mimetype='application/javascript')
    else:
        return render_to_response("image_edit_basic.html",
            {"image":image,
             "s3_small_thumbnails_bucket":settings.S3_SMALL_THUMBNAILS_BUCKET,
             "s3_url":settings.S3_URL,
             "form":ImageEditBasicForm(),
             "subjects_prefill":[],
            },
            context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_basic(request, id):
    image = get_object_or_404(Image, pk=id)
    if request.user != image.user:
        return HttpResponseForbidden();

    form = ImageEditBasicForm({'title': image.title,
                               'description': image.description})

    return render_to_response('image_edit_basic.html',
        {'image':image,
         's3_small_thumbnails_bucket':settings.S3_SMALL_THUMBNAILS_BUCKET,
         's3_url':settings.S3_URL,
         'form':form,
         'prefill_dict': {
            'subjects': jsonDump(image.subjects.all()),
            'locations': jsonDump(image.locations.all()),
         }
        },
        context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_gear(request, id):
    profile = UserProfile.objects.get(user=request.user)
    image = Image.objects.get(pk=id)
    if request.user != image.user:
        return HttpResponseForbidden();

    form = ImageEditGearForm()
    response_dict = {
        "form": form,
        "s3_small_thumbnails_bucket":settings.S3_SMALL_THUMBNAILS_BUCKET,
        "s3_url":settings.S3_URL,
    }
    prefill_dict = {}

    for attr in ["imaging_telescopes",
                 "guiding_telescopes",
                 "mounts",
                 "imaging_cameras",
                 "guiding_cameras",
                 "focal_reducers",
                 "software",
                 "filters",
                 "accessories",
                ]:
        imageGear = getattr(image, attr).all()
        prefill_dict[attr] = jsonDump(imageGear)

    response_dict['image'] = image
    response_dict['prefill_dict'] = prefill_dict

    return render_to_response("image_edit_gear.html",
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_acquisition(request, id):
    image = Image.objects.get(pk=id)
    if request.user != image.user:
        return HttpResponseForbidden();

    deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=image)
    solar_system_acquisition = None
    image_type = None

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=image)
    except:
        pass

    if deep_sky_acquisitions:
        image_type = 'deep_sky'
    elif solar_system_acquisition:
        image_type = 'solar_system'

    response_dict = {
        'image': image,
        'image_type': image_type,
        'deep_sky_acquisitions': deep_sky_acquisitions,
        'solar_system_acquisition': solar_system_acquisition,
        's3_small_thumbnails_bucket':settings.S3_SMALL_THUMBNAILS_BUCKET,
        's3_url':settings.S3_URL,
    }
    return render_to_response('image_edit_acquisition.html',
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_POST
def image_edit_save_basic(request):
    form = ImageEditBasicForm(request.POST)
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)
    if request.user != image.user:
        return HttpResponseForbidden();

    response_dict = {'form': form,
                     'image': image,
                     's3_small_thumbnails_bucket':settings.S3_SMALL_THUMBNAILS_BUCKET,
                     's3_url':settings.S3_URL,
                    }
    prefill_dict = {}

    if not form.is_valid():
        return render_to_response("image_edit_basic.html",
            response_dict,
            context_instance=RequestContext(request))

    image.subjects.clear()
    image.locations.clear()

    for i in [[image.subjects, 'subjects', Subject],
              [image.locations, 'locations', Location]]:
        reader = csv.reader([request.POST['as_values_' + i[1]]],
                            skipinitialspace = True)
        for row in reader:
            for name in row:
                if name != '':
                    k, created = i[2].objects.get_or_create(name = name)
                    if created:
                        k.save()
                    i[0].add(k)
        prefill_dict[i[1]] = jsonDump(i[0].all())

    image.title = form.cleaned_data['title'] 
    image.description = form.cleaned_data['description']

    image.save()
    response_dict['prefill_dict'] = prefill_dict

    return render_to_response("image_edit_basic.html",
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_POST
def image_edit_save_gear(request):
    profile = UserProfile.objects.get(user = request.user)
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)
    if request.user != image.user:
        return HttpResponseForbidden();

    image.imaging_telescopes.clear()
    image.guiding_telescopes.clear()
    image.mounts.clear()
    image.imaging_cameras.clear()
    image.guiding_cameras.clear()
    image.focal_reducers.clear()
    image.filters.clear()
    image.accessories.clear()

    form = ImageEditGearForm()
    response_dict = {'form': form,
                     's3_small_thumbnails_bucket':settings.S3_SMALL_THUMBNAILS_BUCKET,
                     's3_url':settings.S3_URL,
                    }
    prefill_dict = {}

    data = {} 
    for k, v in {"imaging_telescopes": [Telescope, profile.telescopes, "telescopes"],
                 "guiding_telescopes": [Telescope, profile.telescopes, "telescopes"],
                 "mounts"            : [Mount, profile.mounts],
                 "imaging_cameras"   : [Camera, profile.cameras, "cameras"],
                 "guiding_cameras"   : [Camera, profile.cameras, "cameras"],
                 "focal_reducers"    : [FocalReducer, profile.focal_reducers],
                 "software"          : [Software, profile.software],
                 "filters"           : [Filter, profile.filters],
                 "accessories"       : [Accessory, profile.accessories],
                }.iteritems():
        data[k] = csv.reader([request.POST['as_values_' + k]], skipinitialspace = True)
        for row in data[k]:
            for name in row:
                if name != '':
                    gear_item, created = v[1].get_or_create(name = name)
                    if created:
                        gear_item.save()
                        getattr(profile, v[2] if len(v) > 2 else k).add(gear_item)
                        profile.save()
                    getattr(image, k).add(gear_item)

        imageGear = getattr(image, k).all()
        prefill_dict[k] = jsonDump(imageGear)

    image.save()
    response_dict['image'] = image
    response_dict['prefill_dict'] = prefill_dict

    return render_to_response("image_edit_gear.html",
        response_dict,
        context_instance=RequestContext(request))


@login_required
@require_POST
def image_edit_save_acquisition(request):
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)
    if request.user != image.user:
        return HttpResponseForbidden();

    image_type = request.POST.get('image_type')

    deep_sky_acquisitions = {}
    solar_system_acquisition = None

    for a in DeepSky_Acquisition.objects.filter(image=image):
        a.delete()
    for a in SolarSystem_Acquisition.objects.filter(image=image):
        a.delete()

    if image_type == 'deep_sky':
        from collections import defaultdict
        deep_sky_acquisitions = defaultdict(DeepSky_Acquisition)
        for field, value in request.POST.iteritems():
            if field[1] == '_':
                acquisition_type, sequence_number, attribute = field.split('_')
                if attribute == 'date' and value == 'yyyy-mm-dd':
                    value = '';
                if value != '':
                    setattr(deep_sky_acquisitions[int(sequence_number)], attribute, value)
                setattr(deep_sky_acquisitions[int(sequence_number)], 'acquisition_type', acquisition_type)

        for a in deep_sky_acquisitions.values():
            a.image = image
            a.save()
    elif image_type == 'solar_system':
        date = request.POST.get('date')
        if date == 'yyyy-mm-dd':
            date = None

        time = request.POST.get('time')
        if time == 'hh:mm':
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

        solar_system_acquisition.save()

    # get them again because of date issues
    deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=image)
    solar_system_acquisition = None

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=image)
    except:
        pass

    response_dict = {
        'image': image,
        'image_type': image_type,
        'deep_sky_acquisitions': deep_sky_acquisitions,
        'solar_system_acquisition': solar_system_acquisition,
        's3_small_thumbnails_bucket':settings.S3_SMALL_THUMBNAILS_BUCKET,
        's3_url':settings.S3_URL,
    }

    return render_to_response('image_edit_acquisition.html',
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_GET
def image_delete(request, id):
    image = get_object_or_404(Image, pk=id) 
    if request.user != image.user:
        return HttpResponseForbidden();

    image.delete()
    return render_to_response("user_page.html",
        {'user': request.user},
        context_instance=RequestContext(request))


@require_GET
def user_page(request, username):
    """Shows the user's public page"""

    user = User.objects.get(username=username)

    return object_list(
        request, 
        queryset=Image.objects.filter(user=user)[:8],
        template_name='user_page.html',
        template_object_name='image',
        extra_context = {"thumbnail_size":settings.THUMBNAIL_SIZE,
                         "s3_thumbnails_bucket":settings.S3_THUMBNAILS_BUCKET,
                         "s3_abpod_bucket":settings.S3_ABPOD_BUCKET,
                         "s3_url":settings.S3_URL,
                         "user":user})


@login_required
@require_GET
def user_profile_edit_basic(request):
    """Edits own profile"""
    profile = UserProfile.objects.get(user = request.user)
    form = UserProfileEditBasicForm(instance = profile)
    response_dict = {
        'form': form,
        'prefill_dict': {'locations': jsonDump(profile.locations.all())}
    }
    return render_to_response("user_profile_edit_basic.html",
        response_dict,
        context_instance=RequestContext(request))


@login_required
@require_POST
def user_profile_save_basic(request):
    """Saves the form"""

    form = UserProfileEditBasicForm(request.POST)
    response_dict = {'form': form}

    if form.is_valid():
        profile = UserProfile.objects.get(user = request.user)
        profile.locations.clear()
        reader = csv.reader([request.POST['as_values_locations']],
                            skipinitialspace = True)
        for row in reader:
            for name in row:
                if name != '':
                    location, created = Location.objects.get_or_create(name = name)
                    if created:
                        location.save()
                    profile.locations.add(location)

        profile.website  = form.cleaned_data['website']
        profile.job      = form.cleaned_data['job']
        profile.hobbies  = form.cleaned_data['hobbies']

        profile.save()

    response_dict['prefill_dict'] = {'locations': jsonDump(profile.locations.all()) }
    return render_to_response("user_profile_edit_basic.html",
        response_dict,
        context_instance=RequestContext(request))
 
 
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

    response_dict['prefill_dict'] = prefill_dict
    return render_to_response("user_profile_edit_gear.html",
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

    form = UserProfileEditGearForm()
    response_dict = {"form": form}
    prefill_dict = {}

    data = {} 
    for k, v in {"telescopes"    : [Telescope, profile.telescopes],
                 "mounts"        : [Mount, profile.mounts],
                 "cameras"       : [Camera, profile.cameras],
                 "focal_reducers": [FocalReducer, profile.focal_reducers],
                 "software"      : [Software, profile.software],
                 "filters"       : [Filter, profile.filters],
                 "accessories"   : [Accessory, profile.accessories],
                }.iteritems():
        data[k] = csv.reader([request.POST['as_values_' + k]], skipinitialspace = True)
        for row in data[k]:
            for name in row:
                if name != '':
                    gear_item, created = v[0].objects.get_or_create(name = name)
                    if created:
                        gear_item.save()
                    getattr(profile, k).add(gear_item)

        allGear = getattr(profile, k).all()
        prefill_dict[k] = jsonDump(allGear)

    profile.save()

    response_dict['prefill_dict'] = prefill_dict
    return render_to_response("user_profile_edit_gear.html",
        response_dict,
        context_instance=RequestContext(request))


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
        response_dict['flickr_link'] = link;
        return render_to_response("user_profile_flickr_import.html",
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
            request.session['current-progress'] = [0, 'Importing images...']
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
                    file = urllib.urlopen(source)
                    s3_filename = str(uuid4()) + '.JPG'
                    store_image_in_s3(file, s3_filename, 'image/jpeg')
                    image = Image(filename = s3_filename, user = request.user,
                                  title = title if title is not None else '',
                                  description = description if description is not None else '')
                    image.save()
                    if index > 0:
                        request.session['current-progress'] = [100 / index / len(selected_photos), photo_id]

        return HttpResponse(simplejson.dumps(response_dict),
                            mimetype='application/javascript')

    return render_to_response("user_profile_flickr_import.html",
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


def request_progress(request):
    """
    Return JSON object with information about the progress of an upload.
    """
    progress_id = None
    if 'X-Progress-ID' in request.GET:
        progress_id = request.GET['X-Progress-ID']
    elif 'X-Progress-ID' in request.META:
        progress_id = request.META['X-Progress-ID']
    if progress_id:
        cache_key = "%s_%s" % (request.META['REMOTE_ADDR'], progress_id)
        data = cache.get(cache_key)
        json = simplejson.dumps(data)
        return HttpResponse(json)
    else:
        return HttpResponseBadRequest('Server Error: You must provide X-Progress-ID header or query param.')
