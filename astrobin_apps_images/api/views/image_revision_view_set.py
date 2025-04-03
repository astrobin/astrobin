# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from rest_framework.viewsets import GenericViewSet

from astrobin.models import Image, ImageRevision
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
    http_method_names = ['get', 'head', 'put', 'patch', 'delete']

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True

        # Doing these manually because we don't have a CamelCaseJSONParser here.

        if 'squareCropping' in request.data:
            request.data['square_cropping'] = request.data.pop('squareCropping')

        if 'mouseHoverImage' in request.data:
            request.data['mouse_hover_image'] = request.data.pop('mouseHoverImage')

        if 'loopVideo' in request.data:
            request.data['loop_video'] = request.data.pop('loopVideo')

        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.thumbnail_invalidate()
        super().perform_destroy(instance)

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
        
    @action(detail=True, methods=['patch'], url_path='set-annotations')
    def set_annotations(self, request, pk=None):
        revision = self.get_object()
        
        if not request.user.is_authenticated:
            return Response("Authentication required", status=HTTP_401_UNAUTHORIZED)
            
        if not request.user.is_superuser and revision.image.user != request.user:
            return Response("Permission denied", status=HTTP_403_FORBIDDEN)
            
        annotations = request.data.get('annotations')
        if annotations is None:
            return Response("Annotations field is required", status=HTTP_400_BAD_REQUEST)
            
        from django.utils import timezone
        now = timezone.now()
        # Use queryset update to avoid triggering signals and other side effects
        ImageRevision.objects.filter(pk=revision.pk).update(
            annotations=annotations,
        )
        
        # Update the parent image's updated field too
        Image.objects_including_wip.filter(pk=revision.image.pk).update(
            updated=now
        )
        
        # Refresh the object from the database
        revision.refresh_from_db()
        serializer = self.get_serializer(revision)
        return Response(serializer.data, status=HTTP_200_OK)
