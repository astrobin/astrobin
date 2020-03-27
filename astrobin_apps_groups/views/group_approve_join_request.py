from braces.views import JSONResponseMixin, LoginRequiredMixin
from django.conf import settings
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.views.generic import UpdateView

from astrobin.models import UserProfile
from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictToModeratedGroupsMixin, RestrictToGroupModeratorsMixin
from astrobin_apps_notifications.utils import push_notification


class GroupApproveJoinRequestView(JSONResponseMixin, LoginRequiredMixin,
                                  RestrictToModeratedGroupsMixin, RestrictToGroupModeratorsMixin,
                                  UpdateView):
    model = Group

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            user = UserProfile.objects.get(user__pk=self.request.POST.get('user')).user

            if user not in group.join_requests.all():
                return HttpResponseForbidden()

            group.join_requests.remove(user)
            group.members.add(user)
            push_notification([user], 'group_join_request_approved',
                              {
                                  'group_name': group.name,
                                  'url': settings.BASE_URL + reverse('group_detail', args=(group.pk,)),
                              })

            return self.render_json_response({
                'member': user.pk,
            })

        # Only AJAX allowed
        return HttpResponseForbidden()
