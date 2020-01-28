from django.db.models import Q
from django.views.generic import ListView

from astrobin_apps_groups.models import Group


class GroupListView(ListView):
    model = Group
    template_name = 'astrobin_apps_groups/group_list.html'

    def get_context_data(self, **kwargs):
        context = super(GroupListView, self).get_context_data(**kwargs)

        sort = self.request.GET.get('sort', 'activity')
        try:
            sort = {
                'name': 'name',
                'category': 'category',
                'created': '-date_created',
                'activity': '-date_updated',
                'posts': '-forum__post_count',
            }[sort]
        except KeyError:
            pass

        if self.request.user.is_authenticated():
            context['private_groups'] = \
                self.get_queryset() \
                    .filter(public=False) \
                    .filter(
                    Q(owner=self.request.user) |
                    Q(members=self.request.user) |
                    Q(invited_users=self.request.user)) \
                    .distinct() \
                    .order_by(sort)

        context['public_groups'] = \
            self.get_queryset().filter(public=True).order_by(sort)

        return context
