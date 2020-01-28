from braces.views import JSONResponseMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import UpdateView

from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictToGroupOwnerMixin, RedirectToGroupDetailMixin


class GroupRevokeInvitationView(
    JSONResponseMixin, LoginRequiredMixin, RestrictToGroupOwnerMixin,
    RedirectToGroupDetailMixin, UpdateView):
    model = Group
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        group = self.get_object()
        user = get_object_or_404(User, username=request.POST.get('user'))
        group.invited_users.remove(user)

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
