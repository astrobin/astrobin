from braces.views import LoginRequiredMixin
from django.views.generic import DetailView

from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictPrivateGroupToMembersMixin


class GroupMembersListView(LoginRequiredMixin, RestrictPrivateGroupToMembersMixin, DetailView):
    model = Group
    template_name = 'astrobin_apps_groups/group_members_list.html'

    def get_context_data(self, **kwargs):
        context = super(GroupMembersListView, self).get_context_data(**kwargs)
        group = self.get_object()
        context['members'] = group.members.all().order_by('username')
        return context
