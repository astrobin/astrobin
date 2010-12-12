from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
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

from models import Image
from models import ABPOD
from models import UserProfile
from models import Telescope
from models import Mount
from models import Camera
from models import FocalReducer
from forms import ImageUploadForm
from forms import ImageUploadDetailsForm
from forms import UserProfileEditBasicForm
from forms import UserProfileEditGearForm
from file_utils import store_image_in_s3

def jsonGearDump(allGear):
    return simplejson.dumps([{'value_unused': g.id, 'name': g.name} for g in allGear])

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

    form = ImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return render_to_response("image_upload.html", {"form":form})

    file = request.FILES["file"]
    s3_filename = str(uuid4()) + os.path.splitext(file.name)[1]
    store_image_in_s3(file, s3_filename)

    image = Image(filename = s3_filename)
    image.save()

    return render_to_response("image_upload_phase_2.html",
        {"image":image,
         "s3_images_bucket":settings.S3_IMAGES_BUCKET,
         "s3_url":settings.S3_URL,
         "form":ImageUploadDetailsForm(),
        },
        context_instance=RequestContext(request))

@login_required
@require_POST
def image_upload_process_details(request):
    """Process the second part of the form"""

    form = ImageUploadDetailsForm(request.POST)
    image_id = request.POST.get('image_id')
    image = Image.objects.get(pk=image_id)

    if not form.is_valid():
        return render_to_response("image_upload_phase_2.html",
            {"image":image,
             "s3_images_bucket":settings.S3_IMAGES_BUCKET,
             "s3_url":settings.S3_URL,
             "form":form,
            },
            context_instance=RequestContext(request))

    image.subjects = form.cleaned_data['subjects']
    image.camera = form.cleaned_data['camera']
    image.focal_reducer = form.cleaned_data['focal_reducer']
    image.telescope = form.cleaned_data['telescope']
    image.mount = form.cleaned_data['mount']
    image.description = form.cleaned_data['description']

    image.save()

    return HttpResponseRedirect("/show/" + image_id)

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
    formContent = {"form": form}

    for attr in ["telescopes", "mounts", "cameras", "focal_reducers"]:
        allGear = getattr(profile, attr).all()
        formContent[attr + "_prefill"] = jsonGearDump(allGear)

    return render_to_response("user_profile_edit_gear.html",
                              formContent,
                              context_instance=RequestContext(request))

@login_required
@require_POST
def user_profile_save_gear(request):
    """Saves the form"""

    import csv

    profile = UserProfile.objects.get(user = request.user)

    profile.telescopes.clear()
    profile.mounts.clear()
    profile.cameras.clear()
    profile.focal_reducers.clear()

    form = UserProfileEditGearForm()
    formContent = {"form": form}

    data = {} 
    for k, v in {"telescopes"    : [Telescope, profile.telescopes],
                 "mounts"        : [Mount, profile.mounts],
                 "cameras"       : [Camera, profile.cameras],
                 "focal_reducers": [FocalReducer, profile.focal_reducers]}.iteritems():
        data[k] = csv.reader([request.POST['as_values_' + k]], skipinitialspace = True)
        for row in data[k]:
            for name in row:
                if name != '':
                    gear_item, created = v[0].objects.get_or_create(name = name)
                    if created:
                        gear_item.save()
                    getattr(profile, k).add(gear_item)

        allGear = getattr(profile, k).all()
        formContent[k + "_prefill"] = jsonGearDump(allGear)

    profile.save()

    return render_to_response("user_profile_edit_gear.html",
        formContent,
        context_instance=RequestContext(request))

