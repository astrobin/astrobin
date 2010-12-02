from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic.list_detail import object_list
from django.views.generic.list_detail import object_detail
from django.views.generic.create_update import create_object
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from uuid import uuid4
import os

from models import Image
from forms import ImageUploadForm
from forms import ImageUploadDetailsForm
from file_utils import store_in_s3

def index(request):
    return HttpResponse("Hello, World.")

def image_list(request):
    """ List all images"""

    return object_list(
        request, 
        queryset=Image.objects.all(),
        template_name='image_list.html',
        template_object_name='image')

def image_detail(request, id):
    """ Show details of an image"""

    return object_detail(
        request,
        queryset = Image.objects.all(),
        object_id = id,
        template_name = 'image_detail.html',
        template_object_name = 'image')

def image_upload(request):
    """Create new image"""

    return render_to_response(
        "image_upload.html",
        {"form":ImageUploadForm()})

@require_POST
def image_upload_process(request):
    """Process the form"""

    form = ImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return render_to_response("image_upload.html", {"form":form})

    file = request.FILES["file"]
    s3_filename = str(uuid4()) + os.path.splitext(file.name)[1]
    store_in_s3(file, s3_filename, settings.S3_IMAGES_BUCKET)

    image = Image(filename = s3_filename)
    image.save()

    return render_to_response("image_upload_phase_2.html",
        {"image":image,
         "s3_images_bucket":settings.S3_IMAGES_BUCKET,
         "s3_url":settings.S3_URL,
         "form":ImageUploadDetailsForm(),
        })

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
            })

