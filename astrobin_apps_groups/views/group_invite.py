from braces.views import JSONResponseMixin, LoginRequiredMixin
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import UpdateView

from astrobin.models import UserProfile
from astrobin_apps_groups.forms import GroupInviteForm
from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictToGroupOwnerMixin, RedirectToGroupDetailMixin
from astrobin_apps_notifications.utils import push_notification


class GroupInviteView(
    JSONResponseMixin, LoginRequiredMixin, RestrictToGroupOwnerMixin,
    RedirectToGroupDetailMixin, UpdateView):
    form_class = GroupInviteForm
    model = Group
    template_name = 'astrobin_apps_groups/group_invite.html'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        group = self.get_object()
        for pk in request.POST.getlist('users[]'):
            try:
                user = UserProfile.objects.get(user__pk=pk).user
            except UserProfile.DoesNotExist:
                continue

            group.invited_users.add(user)
            push_notification([user], 'new_group_invitation',
                              {
                                  'inviter': request.user.userprofile.get_display_name(),
                                  'inviter_page': reverse('user_page', args=(request.user.username,)),
                                  'group_name': group.name,
                                  'group_page': settings.BASE_URL + reverse('group_detail', args=(group.pk,)),
                              })

        if request.is_ajax():
            return self.render_json_response({
                'invited_users': [{
                    'id': x.id,
                    'username': x.username,
                    'display_name': x.userprofile.get_display_name(),
                    'url': reverse('user_page', args=(x.username,)),
                    'revoke_url': reverse('group_revoke_invitation', args=(group.pk,)),
                } for x in group.invited_users.all()]
            })

        return redirect(self.get_success_url())
