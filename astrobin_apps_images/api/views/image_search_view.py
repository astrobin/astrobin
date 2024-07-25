from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_haystack.filters import HaystackFilter, HaystackOrderingFilter
from drf_haystack.viewsets import HaystackViewSet
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.throttling import ScopedRateThrottle

from astrobin.models import Image
from astrobin_apps_images.api.serializers import ImageSearchSerializer
from common.api_page_size_pagination import PageSizePagination
from common.permissions import ReadOnly
from common.services.search_service import SearchService


class ImageSearchView(HaystackViewSet):
    index_models = [Image]
    serializer_class = ImageSearchSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]
    filter_backends = (HaystackFilter, HaystackOrderingFilter)
    ordering_fields = ('published', 'title', 'w', 'h', 'likes')
    ordering = ('-published',)
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'search'
    pagination_class = PageSizePagination


    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        # Composite filters
        queryset = SearchService.filter_by_subject(self.request.query_params, queryset)

        return queryset
