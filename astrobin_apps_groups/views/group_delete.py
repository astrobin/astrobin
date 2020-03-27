from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import DeleteView

from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.group_update import GroupUpdateView
from astrobin_apps_groups.views.mixins import RestrictToGroupOwnerMixin


class GroupDeleteView(LoginRequiredMixin, RestrictToGroupOwnerMixin, DeleteView):
    model = Group
    success_url = reverse_lazy('group_list')

    def form_valid(self, form):
        messages.success(self.request, _("Group deleted"))
        return super(GroupUpdateView, self).form_valid(form)
