from django.conf import settings
from django.db.models import Q
from django.views import generic
from pybb.models import Topic
from pybb.views import PaginatorMixin


class LatestTopicsView(PaginatorMixin, generic.ListView):
    paginate_by = settings.PYBB_TOPIC_PAGE_SIZE
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

        qs = qs.select_related()

        return qs.order_by('-updated', '-id')[:settings.PYBB_TOPIC_PAGE_SIZE * 2]
