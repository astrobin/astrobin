from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import UpdateView

from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RedirectToGroupDetailMixin, RestrictToGroupMembersMixin


class GroupLeaveView(
    LoginRequiredMixin, RedirectToGroupDetailMixin,
    RestrictToGroupMembersMixin, UpdateView):
    http_method_names = ['post', ]
    model = Group

    def post(self, request, *args, **kwargs):
        group = self.get_object()

        if request.user not in group.members.all():
            return HttpResponseForbidden()

        group.members.remove(request.user)
        messages.success(request, _("You have left the group"))

        if group.public:
            return redirect(self.get_success_url())
        return redirect(reverse('group_list'))
