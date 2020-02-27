from braces.views import JSONResponseMixin
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render
from django.views.generic import base
from toggleproperties.models import ToggleProperty

from astrobin.models import UserProfile


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

        return render(request, 'astrobin_apps_users/inclusion_tags/user_list.html', context)


class UserSearchView(JSONResponseMixin, base.View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        term = request.GET.get('term')

        profiles = UserProfile.objects.filter(
            Q(user__first_name__icontains=term)|
            Q(user__last_name__icontains=term)|
            Q(user__username__icontains=term)|
            Q(real_name__icontains=term))

        if request.is_ajax():
            matches = []
            for profile in profiles:
                matches.append({
                    'id': profile.user.pk,
                    'username': profile.user.username,
                    'display_name': profile.get_display_name(),
                    'url': reverse('user_page', args = (profile.user.username,)),
                })

            return self.render_json_response(matches)
