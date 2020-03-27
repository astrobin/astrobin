from braces.views import LoginRequiredMixin
from django.views.generic import UpdateView

from astrobin_apps_groups.forms import GroupInviteForm
from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictToGroupOwnerMixin, RedirectToGroupDetailMixin


class GroupManageMembersView(LoginRequiredMixin, RestrictToGroupOwnerMixin, RedirectToGroupDetailMixin, UpdateView):
    form_class = GroupInviteForm
    model = Group
    template_name = 'astrobin_apps_groups/group_manage_members.html'
