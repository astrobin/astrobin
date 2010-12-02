from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic.list_detail import object_list
from django.views.generic.list_detail import object_detail
from django.views.generic.create_update import create_object
from django.core.urlresolvers import reverse

from uuid import uuid4
import os

from models import Image
from forms import ImageUploadForm
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

def image_upload_process(request):
    """Process the form"""

    form = ImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return render_to_response("image_upload.html", {"form":form})

    file = request.FILES["file"]
    s3_filename = str(uuid4()) + os.path.splitext(file.name)[1]
    store_in_s3(file, s3_filename)

    image = Image(url = "http://astrobin_images.s3.amazonaws.com/" + s3_filename)
    image.save()

    return render_to_response("image_upload_phase_2.html", {"image":image})
