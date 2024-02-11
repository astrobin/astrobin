from django.conf import settings
from django.contrib.postgres.search import TrigramDistance
from django.core.paginator import Paginator
from django.db.models import Q, QuerySet
from django.db.models.functions import Lower
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from pybb.models import Forum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin.permissions import CustomForumPermissions
from astrobin_apps_forum.api.filters.forum_filter import ForumFilter
from astrobin_apps_forum.api.serializers.forum_serializer import ForumSerializer
from common.permissions import ReadOnly


class ForumViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    serializer_class = ForumSerializer
    permission_classes = [ReadOnly]
    filter_class = ForumFilter
    http_method_names = ['get', 'head']

    def get_queryset(self) -> QuerySet:
        queryset = Forum.objects.filter(hidden=False)
        return CustomForumPermissions().filter_forums(self.request.user, queryset)

    @action(detail=False, methods=['get'])
    def select2(self, request):
        page_size = settings.REST_FRAMEWORK['PAGE_SIZE']

        try:
            page_number = int(request.GET.get('page', 1))
        except ValueError:
            page_number = 1

        q = request.GET.get('q', '')
        is_equipment = request.GET.get('is-equipment')

        if is_equipment:
            is_equipment = is_equipment.lower() == 'true'

        queryset = self.get_queryset()\
            .select_related('category')\
            .exclude(category__slug='group-forums')

        if q:
            queryset = queryset\
                .annotate(distance=TrigramDistance('name', q))\
                .filter(Q(distance__lte=.75) | Q(name__icontains=q))

        # Weird True/False check because is_equipment can be None
        if is_equipment is True:
            queryset = queryset.filter(category__slug='equipment-forums')
            if q:
                queryset = queryset.order_by('distance', Lower('name'))
            else:
                queryset = queryset.order_by(Lower('name'))
        elif is_equipment is False:
            queryset = queryset\
                .exclude(category__slug='equipment-forums')\
                .order_by('category__position', 'position')[:20]
        else:
            queryset = queryset.order_by('category__position', 'position')[:20]

        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)

        return Response(
            {
                'total_count': paginator.count,
                'items': [
                    {'id': item.id, 'text': item.name} for item in page
                ],
            }
        )
