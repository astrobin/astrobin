from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_haystack.filters import HaystackFilter, HaystackOrderingFilter
from drf_haystack.viewsets import HaystackViewSet
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.throttling import ScopedRateThrottle

from astrobin.models import Image
from astrobin_apps_images.api.serializers import ImageSearchSerializer
from common.permissions import ReadOnly


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
