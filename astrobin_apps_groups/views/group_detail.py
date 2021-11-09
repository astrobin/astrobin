from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView
from pybb.permissions import perms

from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictPrivateGroupToMembersMixin


class GroupDetailView(RestrictPrivateGroupToMembersMixin, DetailView):
    model = Group

    def get_template_names(self):
        if self.request.is_ajax():
            return 'inclusion_tags/image_list_entries.html'
        return 'astrobin_apps_groups/group_detail.html'

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('slug') is None:
            group = self.get_object()
            return HttpResponseRedirect(reverse('group_detail', args=(group.pk, group.slug)))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GroupDetailView, self).get_context_data(**kwargs)
        group = self.get_object()

        images = group.images.all()
        sort = self.request.GET.get('sort', group.default_image_sorting)
        if sort == 'title':
            images = images.order_by('title')
        elif sort == 'publication':
            images = images.order_by('-published')

        # Images
        context['image_list'] = images
        context['alias'] = 'gallery'
        context['paginate_by'] = settings.PAGINATE_GROUP_DETAIL_PAGE_BY

        # Misc
        context['user_is_member'] = self.request.user in group.members.all()
        context['user_is_invited'] = self.request.user in group.invited_users.all()
        context['user_is_moderator'] = self.request.user in group.moderators.all()

        # Forum
        topics = group.forum.topics.order_by('-sticky', '-updated', '-id').select_related()
        topics = perms.filter_topics(self.request.user, topics)
        context['topics'] = topics[:25]

        return context
