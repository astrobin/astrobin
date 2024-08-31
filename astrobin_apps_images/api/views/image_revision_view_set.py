# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.viewsets import GenericViewSet

from astrobin.models import ImageRevision
from astrobin_apps_images.api.filters import ImageRevisionFilter
from astrobin_apps_images.api.permissions import IsImageOwnerOrReadOnly
from astrobin_apps_images.api.serializers import ImageRevisionSerializer
from astrobin_apps_images.services import ImageService


class ImageRevisionViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
    mixins.ListModelMixin, GenericViewSet
):
    serializer_class = ImageRevisionSerializer
    queryset = ImageRevision.objects.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    filter_class = ImageRevisionFilter
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsImageOwnerOrReadOnly
    ]
    http_method_names = ['get', 'head', 'put', 'patch']

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True

        # Doing these manually because we don't have a CamelCaseJSONParser here.

        if 'squareCropping' in request.data:
            request.data['square_cropping'] = request.data.pop('squareCropping')

        if 'mouseHoverImage' in request.data:
            request.data['mouse_hover_image'] = request.data.pop('mouseHoverImage')

        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['get'], url_path='video-encoding-progress')
    def video_encoding_progress(self, request, pk=None):
        content_type = ContentType.objects.get_for_model(ImageRevision)

        value = cache.get(f"video-encoding-progress-{content_type.pk}-{pk}")

        return Response(value, HTTP_200_OK)

    @action(detail=True, methods=['put'], url_path='mark-as-final')
    def mark_as_final(self, request, pk=None):
        revision: ImageRevision = self.get_object()

        ImageService(revision.image).mark_as_final(revision.label)

        return Response(status=HTTP_200_OK)
