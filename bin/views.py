from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.generic.list_detail import object_list
from django.views.generic.list_detail import object_detail
from django.views.generic.create_update import create_object
from django.core.urlresolvers import reverse

from models import Image

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

def image_create(request):
	"""Create new image"""

    #return render_to_response("create.html"
