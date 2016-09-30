# Python
import simplejson

# Django
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import base

# Third party
from braces.views import JSONResponseMixin
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
            'user_list': users,
            'view': 'table',
            'layout': 'compact',
        }

        return render_to_response(
            'astrobin_apps_users/inclusion_tags/user_list.html',
            context,
            context_instance = RequestContext(request))


class UserSearchView(JSONResponseMixin, base.View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        term = request.GET.get('term')

        users = User.objects.filter(
            Q(first_name__icontains=term)|
            Q(last_name__icontains=term)|
            Q(username__icontains=term)|
            Q(userprofile__real_name__icontains=term))

        if request.is_ajax():
            matches = []
            for user in users:
                matches.append({
                    'id': user.pk,
                    'username': user.username,
                    'display_name': user.userprofile.get_display_name(),
                    'url': reverse('user_page', args = (user.username,)),
                })

            return self.render_json_response(matches)
