from django.http import HttpResponse
from django.http import HttpResponseRedirect
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
    return simplejson.dumps([{'value_unused': i.id, 'name': i.name} for i in all])


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
                         "abpod":abpod})


def image_detail(request, id):
    """ Show details of an image"""

    return object_detail(
        request,
        queryset = Image.objects.all(),
        object_id = id,
        template_name = 'image_detail.html',
        template_object_name = 'image',
        extra_context = {"s3_images_bucket":settings.S3_IMAGES_BUCKET,
                         "s3_resized_images_bucket":settings.S3_RESIZED_IMAGES_BUCKET,
                         "s3_thumbnails_bucket":settings.S3_THUMBNAILS_BUCKET,
                         "s3_small_thumbnails_bucket":settings.S3_SMALL_THUMBNAILS_BUCKET,
                         "s3_inverted_bucket":settings.S3_INVERTED_BUCKET,
                         "s3_resized_inverted_bucket":settings.S3_RESIZED_INVERTED_BUCKET,
                         "s3_url":settings.S3_URL})


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
            return render_to_response("image_upload.html", {"form":form})
        file = request.FILES["file"]

    s3_filename = str(uuid4()) + os.path.splitext(file.name)[1]
    store_image_in_s3(file, s3_filename)

    image = Image(filename = s3_filename)
    image.save()

    if 'qqfile' in request.GET:
        return_dict = {'success':'true', 'id':image.id}
        return HttpResponse(simplejson.dumps(return_dict),
                            mimetype='application/javascript')
    else:
        return render_to_response("image_edit_basic.html",
            {"image":image,
             "s3_images_bucket":settings.S3_IMAGES_BUCKET,
             "s3_url":settings.S3_URL,
             "form":ImageEditBasicForm(),
             "subjects_prefill":[],
            },
            context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_basic(request, id):
    image = get_object_or_404(Image, pk=id)
    form = ImageEditBasicForm({'title': image.title,
                               'description': image.description})

    return render_to_response("image_edit_basic.html",
        {"image":image,
         "s3_images_bucket":settings.S3_IMAGES_BUCKET,
         "s3_url":settings.S3_URL,
         "form":form,
         "subjects_prefill":jsonDump(image.subjects.all()),
        },
        context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_gear(request, id):
    profile = UserProfile.objects.get(user=request.user)
    image = Image.objects.get(pk=id)
    form = ImageEditGearForm()
    response_dict = {"form": form}

    for attr in ["imaging_telescopes",
                 "guiding_telescopes",
                 "mounts",
                 "imaging_cameras",
                 "guiding_cameras",
                 "focal_reducers",
                 "software",
                 "filters"]:
        imageGear = getattr(image, attr).all()
        response_dict[attr + "_prefill"] = jsonDump(imageGear)

    response_dict['image'] = image

    return render_to_response("image_edit_gear.html",
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_GET
def image_edit_acquisition(request, id):
    image = Image.objects.get(pk=id)
    form = ImageEditAcquisitionForm()
    response_dict = {'form': form, 'image': image}
    return render_to_response('image_edit_acquisition.html',
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_POST
def image_edit_save_basic(request):
    form = ImageEditBasicForm(request.POST)
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)

    response_dict = {'form': form,
                     'image': image,
                     'subjects_prefill': jsonDump(image.subjects.all())}

    if not form.is_valid():
        return render_to_response("image_edit_basic.html",
            response_dict,
            context_instance=RequestContext(request))

    reader = csv.reader([request.POST['as_values_subjects']],
                        skipinitialspace = True)
    for row in reader:
        for name in row:
            if name != '':
                subject, created = Subject.objects.get_or_create(name = name)
                if created:
                    subject.save()
                image.subjects.add(subject)

    if form.is_valid():
        image.title = form.cleaned_data['title'] 
        image.description = form.cleaned_data['description']

    image.save()
    response_dict['subject_prefill'] = jsonDump(image.subjects.all())

    return render_to_response("image_edit_basic.html",
                              response_dict,
                              context_instance=RequestContext(request))


@login_required
@require_POST
def image_edit_save_gear(request):
    profile = UserProfile.objects.get(user = request.user)
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)

    image.imaging_telescopes.clear()
    image.guiding_telescopes.clear()
    image.mounts.clear()
    image.imaging_cameras.clear()
    image.guiding_cameras.clear()
    image.focal_reducers.clear()
    image.filters.clear()

    form = ImageEditGearForm()
    response_dict = {"form": form}

    data = {} 
    for k, v in {"imaging_telescopes": [Telescope, profile.telescopes, "telescopes"],
                 "guiding_telescopes": [Telescope, profile.telescopes, "telescopes"],
                 "mounts"            : [Mount, profile.mounts],
                 "imaging_cameras"   : [Camera, profile.cameras, "cameras"],
                 "guiding_cameras"   : [Camera, profile.cameras, "cameras"],
                 "focal_reducers"    : [FocalReducer, profile.focal_reducers],
                 "software"          : [Software, profile.software],
                 "filters"           : [Filter, profile.filters]}.iteritems():
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
        response_dict[k + "_prefill"] = jsonDump(imageGear)

    image.save()
    response_dict['image'] = image
    return render_to_response("image_edit_gear.html",
        response_dict,
        context_instance=RequestContext(request))


@require_GET
def user_page(request, username):
    """Shows the user's public page"""

    user = User.objects.get(username=username)

    return render_to_response("user_page.html",
        {"user":user},
        context_instance=RequestContext(request))


@login_required
@require_GET
def user_profile_edit_basic(request):
    """Edits own profile"""

    profile = UserProfile.objects.get(user = request.user)
    form = UserProfileEditBasicForm(instance = profile)
    return render_to_response("user_profile_edit_basic.html",
        {"form":form},
        context_instance=RequestContext(request))


@login_required
@require_POST
def user_profile_save_basic(request):
    """Saves the form"""

    form = UserProfileEditBasicForm(request.POST)
    if form.is_valid():
        profile = UserProfile.objects.get(user = request.user)
        profile.location = form.cleaned_data['location']
        profile.website  = form.cleaned_data['website']
        profile.job      = form.cleaned_data['job']
        profile.hobbies  = form.cleaned_data['hobbies']

        profile.save()

    return render_to_response("user_profile_edit_basic.html",
        {"form":form},
        context_instance=RequestContext(request))
 
 
@login_required
@require_GET
def user_profile_edit_gear(request):
    """Edits own profile"""
    profile = UserProfile.objects.get(user=request.user)

    form = UserProfileEditGearForm()
    response_dict = {"form": form}

    for attr in ["telescopes", "mounts", "cameras", "focal_reducers", "software", "filters"]:
        allGear = getattr(profile, attr).all()
        response_dict[attr + "_prefill"] = jsonDump(allGear)

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

    form = UserProfileEditGearForm()
    response_dict = {"form": form}

    data = {} 
    for k, v in {"telescopes"    : [Telescope, profile.telescopes],
                 "mounts"        : [Mount, profile.mounts],
                 "cameras"       : [Camera, profile.cameras],
                 "focal_reducers": [FocalReducer, profile.focal_reducers],
                 "software"      : [Software, profile.software],
                 "filters"       : [Filter, profile.filters]}.iteritems():
        data[k] = csv.reader([request.POST['as_values_' + k]], skipinitialspace = True)
        for row in data[k]:
            for name in row:
                if name != '':
                    gear_item, created = v[0].objects.get_or_create(name = name)
                    if created:
                        gear_item.save()
                    getattr(profile, k).add(gear_item)

        allGear = getattr(profile, k).all()
        response_dict[k + "_prefill"] = jsonDump(allGear)

    profile.save()

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
                found_size = False
                for size in sizes.find('sizes').findall('size'):
                    if size.attrib['label'] == 'Original':
                        found_size = True
                        break
                if not found_size:
                    for size in sizes.find('sizes').findall('size'):
                        if size.attrib['label'] == 'Large':
                            found_size = True
                            break
                if found_size:
                    source = size.attrib['source']
                    file = urllib.urlopen(source)
                    s3_filename = str(uuid4())
                    store_image_in_s3(file, s3_filename, 'image/jpeg')
                    image = Image(filename = s3_filename)
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
