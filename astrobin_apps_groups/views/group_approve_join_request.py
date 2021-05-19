import logging

from braces.views import JSONResponseMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, Http404
from django.views.generic import UpdateView

from astrobin_apps_groups.models import Group
from astrobin_apps_groups.tasks import push_notification_for_group_join_request_approval
from astrobin_apps_groups.views.mixins import RestrictToModeratedGroupsMixin, RestrictToGroupModeratorsMixin

logger = logging.getLogger('apps')


class GroupApproveJoinRequestView(JSONResponseMixin, LoginRequiredMixin,
                                  RestrictToModeratedGroupsMixin, RestrictToGroupModeratorsMixin,
                                  UpdateView):
    model = Group

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            user_pk = self.request.POST.get('user')

            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                logger.warning('GroupApproveJoinRequestView: user not found: %d' % user_pk)
                return Http404

            if user not in group.join_requests.all():
                return HttpResponseForbidden()

            group.join_requests.remove(user)
            group.members.add(user)

            push_notification_for_group_join_request_approval.apply_async(args=(group.pk, user.pk, request.user.pk))

            return self.render_json_response({
                'member': user.pk,
            })

        # Only AJAX allowed
        return HttpResponseForbidden()
