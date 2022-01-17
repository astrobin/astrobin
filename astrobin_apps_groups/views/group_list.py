from django.db.models import Count, Q
from django.views.generic import ListView

from astrobin_apps_groups.models import Group


class GroupListView(ListView):
    model = Group
    template_name = 'astrobin_apps_groups/group_list.html'

    def get_context_data(self, **kwargs):
        context = super(GroupListView, self).get_context_data(**kwargs)

        default_sort = 'activity'
        sort = self.request.GET.get('sort', default_sort)
        try:
            sort = {
                'name': 'name',
                'category': 'category',
                'created': '-date_created',
                'activity': '-date_updated',
                'members': '-num_members',
                'images': '-num_images',
                'posts': '-forum__post_count',
            }[sort]
        except KeyError:
            sort = '-date_updated'

        q = self.request.GET.get('q')
        queryset = self.get_queryset().annotate(num_images=Count('images'), num_members=Count('members'))

        if self.request.user.is_authenticated:
            context['owned_private_groups'] = queryset.filter(
                Q(public=False) &
                Q(owner=self.request.user)
            ).order_by(
                sort
            )

            context['member_private_groups'] = queryset.filter(
                Q(public=False) &
                ~Q(owner=self.request.user) &
                Q(members=self.request.user) &
                ~Q(invited_users=self.request.user)
            ).order_by(
                sort
            )

            context['invited_private_groups'] = queryset.filter(
                Q(public=False) &
                ~Q(owner=self.request.user) &
                ~Q(members=self.request.user) &
                Q(invited_users=self.request.user)
            ).order_by(
                sort
            )

            context['owned_public_groups'] = queryset.filter(
                Q(public=True) &
                Q(owner=self.request.user)
            ).order_by(
                sort
            )

            context['member_public_groups'] = queryset.filter(
                Q(public=True) &
                ~Q(owner=self.request.user) &
                Q(members=self.request.user) &
                ~Q(invited_users=self.request.user)
            ).order_by(
                sort
            )

            context['invited_public_groups'] = queryset.filter(
                Q(public=True) &
                ~Q(owner=self.request.user) &
                ~Q(members=self.request.user) &
                Q(invited_users=self.request.user)
            ).order_by(
                sort
            )

            context['public_groups'] = \
                queryset.filter(
                    Q(public=True) &
                    ~Q(owner=self.request.user) &
                    ~Q(members=self.request.user) &
                    ~Q(invited_users=self.request.user)
                ).order_by(
                    sort
                )
        else:
            context['public_groups'] = \
                queryset.filter(
                    public=True
                ).order_by(
                    sort
                )

        if q:
            for x in (
                    'owned_private_groups', 'member_private_groups', 'invited_private_groups',
                    'owned_public_groups', 'member_public_groups', 'invited_public_groups',
                    'public_groups',
            ):
                if x in context:
                    context[x] = context[x].filter(name__icontains=q)

        return context
