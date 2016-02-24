# Python
import simplejson

# Django
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import base

# Third party
from toggleproperties.models import ToggleProperty

class TogglePropertyUsersAjaxView(base.View):
    def get(self, request, *args, **kwargs):
        property_type = kwargs.pop('property_type')
        object_id = kwargs.pop('object_id')
        content_type = ContentType.objects.get_for_id(kwargs.pop('content_type_id'))

        users = [x.user for x in ToggleProperty.objects.filter(
            property_type = property_type,
            object_id = object_id,
            content_type = content_type)]

        context = {
            'layout': 'list',
            'user_list': users,
            'view': 'default',
        }

        return render_to_response(
            'astrobin_apps_users/inclusion_tags/user_list.html',
            context,
            context_instance = RequestContext(request))

