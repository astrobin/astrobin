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

    def get_context_data(self, **kwargs):
        context = super(GroupDetailView, self).get_context_data(**kwargs)
        group = self.get_object()

        # Images
        context['image_list'] = group.images.all()
        context['alias'] = 'gallery'

        # Misc
        context['user_is_member'] = self.request.user in group.members.all()
        context['user_is_invited'] = self.request.user in group.invited_users.all()
        context['user_is_moderator'] = self.request.user in group.moderators.all()

        # Forum
        topics = group.forum.topics.order_by('-sticky', '-updated', '-id').select_related()
        topics = perms.filter_topics(self.request.user, topics)
        context['topics'] = topics[:5]

        return context
