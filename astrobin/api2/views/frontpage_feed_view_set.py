from django.core.cache import cache
from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import permissions, viewsets
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin.api2.serializers.front_page_feed_serializer import FrontPageFeedSerializer
from astrobin.services.activity_stream_service import ActivityStreamService
from astrobin_apps_images.api.serializers.image_serializer_gallery import ImageSerializerGallery
from common.permissions import ReadOnly


class FrontPageFeedViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, ReadOnly)
    serializer_class = FrontPageFeedSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]

    CACHE_TIMEOUT = 60

    def __use_actstream(self):
        return 'recent' not in self.request.query_params and 'followed' not in self.request.query_params

    def __use_image(self):
        return 'recent' in self.request.query_params or 'followed' in self.request.query_params

    def get_serializer_class(self):
        if self.__use_image():
            return ImageSerializerGallery

        return FrontPageFeedSerializer

    def get_queryset(self) -> QuerySet:
        service = ActivityStreamService(self.request.user)
        if 'personal' in self.request.query_params:
            return service.get_personal_stream()

        if 'recent' in self.request.query_params:
            return service.get_recent_images()

        if 'followed' in self.request.query_params:
            return service.get_recent_followed_images()

        return service.get_global_stream()

    def _get_cache_key(self) -> str:
        page = self.request.query_params.get('page', '1')
        base_key = f'front_page_feed:page:{page}'

        params = []
        for param in ['personal', 'recent', 'followed']:
            if param in self.request.query_params:
                params.append(param)

        if params:
            base_key += f':params:{"-".join(sorted(params))}'

        if 'personal' in self.request.query_params or 'followed' in self.request.query_params:
            base_key += f':user:{self.request.user.id}'

        return base_key

    def list(self, request, *args, **kwargs):
        cache_key = self._get_cache_key()
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data)

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data

            cache.set(cache_key, response_data, self.CACHE_TIMEOUT)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response_data = serializer.data
            cache.set(cache_key, response_data, self.CACHE_TIMEOUT)

        return Response(response_data)

    def _get_page_number(self, url):
        """Extract just the page number from a pagination URL"""
        if not url:
            return None
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)
        return query_params.get('page', [None])[0]
