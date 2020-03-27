from braces.views import LoginRequiredMixin
from django.views.generic import DetailView

from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictToModeratedGroupsMixin, RestrictToGroupModeratorsMixin


class GroupModerateJoinRequestsView(LoginRequiredMixin, RestrictToModeratedGroupsMixin,
                                    RestrictToGroupModeratorsMixin, DetailView):
    model = Group
    template_name = 'astrobin_apps_groups/group_moderate_join_requests.html'
