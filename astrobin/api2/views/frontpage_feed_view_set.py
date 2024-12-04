from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import permissions, viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.api2.serializers.front_page_feed_serializer import FrontPageFeedSerializer
from astrobin.services.activity_stream_service import ActivityStreamService
from astrobin_apps_images.api.serializers.image_serializer_gallery import ImageSerializerGallery
from common.permissions import ReadOnly


class FrontPageFeedViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, ReadOnly)
    serializer_class = FrontPageFeedSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]

    def __use_actstream(self):
        return 'recent' not in self.request.query_params and 'followed' not in self.request.query_params

    def __use_image(self):
        return 'recent' in self.request.query_params or 'followed' in self.request.query_params

    def get_serializer_class(self):
        if self.__use_image():
            return ImageSerializerGallery

        return FrontPageFeedSerializer

    def get_queryset(self):
        service = ActivityStreamService(self.request.user)
        if 'personal' in self.request.query_params:
            return service.get_personal_stream()

        if 'recent' in self.request.query_params:
            return service.get_recent_images()

        if 'followed' in self.request.query_params:
            return service.get_recent_followed_images()

        return service.get_global_stream()
