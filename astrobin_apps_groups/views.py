# Django
from django.views.generic import ListView

# This app
from astrobin_apps_groups.models import Group


class PublicGroupListView(ListView):
    model = Group
    template_name = 'astrobin_apps_groups/public_group_list.html'
