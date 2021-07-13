from django.db.models import Q
from django.views import generic
from pybb import defaults
from pybb.models import Topic
from pybb.permissions import perms
from pybb.views import PaginatorMixin


class LatestTopicsView(PaginatorMixin, generic.ListView):
    paginate_by = defaults.PYBB_FORUM_PAGE_SIZE
    context_object_name = 'topic_list'
    template_name = 'pybb/latest_topics.html'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            qs = Topic.objects.filter(
                Q(forum__group=None) |
                Q(forum__group__owner=self.request.user) |
                Q(forum__group__members=self.request.user)
            )
        else:
            qs = Topic.objects.filter(forum__group=None)

        qs = qs\
            .order_by('-updated', '-created', '-id') \
            .distinct() \
            .select_related()

        qs = perms.filter_topics(self.request.user, qs)
        return qs.order_by('-updated', '-id')
