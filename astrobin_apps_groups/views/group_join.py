from braces.views import LoginRequiredMixin
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import UpdateView

from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RedirectToGroupDetailMixin, RestrictToPremiumMembersMixin
from astrobin_apps_notifications.utils import push_notification


class GroupJoinView(LoginRequiredMixin, RedirectToGroupDetailMixin, RestrictToPremiumMembersMixin, UpdateView):
    http_method_names = ['post', ]
    model = Group

    def post(self, request, *args, **kwargs):
        group = self.get_object()

        def doAdd(user, group):
            group.members.add(user)
            group.invited_users.remove(user)
            group.join_requests.remove(user)
            messages.success(request, _("You have joined the group"))

        if request.user in group.members.all():
            messages.error(request, _("You already were a member of this group"))
            return redirect(self.get_success_url())

        if group.public:
            if group.moderated and request.user != group.owner:
                group.join_requests.add(request.user)
                messages.warning(request,
                                 _("This is a moderated group, and your join request will be reviewed by a moderator"))
                push_notification(group.moderators.all(), 'new_group_join_request',
                                  {
                                      'requester': request.user.userprofile.get_display_name(),
                                      'group_name': group.name,
                                      'url': settings.BASE_URL + reverse('group_moderate_join_requests',
                                                                         args=(group.pk,)),
                                  })
                return redirect(self.get_success_url())
            else:
                doAdd(request.user, group)
                return redirect(self.get_success_url())
        else:
            if request.user in group.invited_users.all() or request.user == group.owner:
                doAdd(request.user, group)
                return redirect(self.get_success_url())

        return HttpResponseForbidden()
