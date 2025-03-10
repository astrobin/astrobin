from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView
from pybb.permissions import perms

from astrobin.models import Image
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
        page_size = settings.PAGINATE_GROUP_DETAIL_PAGE_BY

        images = Image.objects.filter(part_of_group_set=group)
        sort = self.request.GET.get('sort', group.default_image_sorting.lower())
        if sort == 'title':
            images = images.order_by('title')
        elif sort == 'publication':
            images = images.order_by('-published')
        elif sort == 'tag':
            images = images.filter(keyvaluetags__key=group.image_tag_sorting).order_by('keyvaluetags__value')

        # Images
        context['image_list'] = images
        context['alias'] = 'gallery'
        context['paginate_by'] = page_size

        # Misc
        context['user_is_member'] = self.request.user in group.members.all()
        context['user_following_images'] = True
        context['user_is_invited'] = self.request.user in group.invited_users.all()
        context['user_is_moderator'] = self.request.user in group.moderators.all()

        # Forum
        topics = group.forum.topics.order_by('-sticky', '-updated', '-id').select_related()
        topics = perms.filter_topics(self.request.user, topics)
        context['topics'] = topics[:25]

        return context
