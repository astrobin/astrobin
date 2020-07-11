# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.metadata import BaseMetadata
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.models import Image
from astrobin_apps_images.api.constants import TUS_API_VERSION, TUS_API_EXTENSIONS, TUS_MAX_FILE_SIZE, \
    TUS_API_CHECKSUM_ALGORITHMS
from astrobin_apps_images.api.filters import ImageFilter
from astrobin_apps_images.api.mixins import TusCreateMixin, TusPatchMixin, TusHeadMixin, TusTerminateMixin
from astrobin_apps_images.api.parsers import TusUploadStreamParser
from astrobin_apps_images.api.permissions import HasUploaderAccessOrReadOnly
from astrobin_apps_images.api.serializers import ImageSerializer


class UploadMetadata(BaseMetadata):
    def determine_metadata(self, request, view):
        return {
            'Tus-Resumable': TUS_API_VERSION,
            'Tus-Version': ','.join([TUS_API_VERSION]),
            'Tus-Extension': ','.join(TUS_API_EXTENSIONS),
            'Tus-Max-Size': getattr(view, 'max_file_size', TUS_MAX_FILE_SIZE),
            'Tus-Checksum-Algorithm': ','.join(TUS_API_CHECKSUM_ALGORITHMS),
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'PATCH,HEAD,GET,POST,OPTIONS',
            'Access-Control-Expose-Headers': 'Tus-Resumable,upload-length,upload-metadata,Location,Upload-Offset',
            'Access-Control-Allow-Headers':
                'Tus-Resumable,upload-length,upload-metadata,Location,Upload-Offset,content-type',
            'Cache-Control': 'no-store'
        }


class ImageViewSet(TusCreateMixin,
                   TusPatchMixin,
                   TusHeadMixin,
                   TusTerminateMixin,
                   viewsets.ModelViewSet):
    serializer_class = ImageSerializer
    queryset = Image.objects_including_wip.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    filter_class = ImageFilter
    metadata_class = UploadMetadata
    parser_classes = [TusUploadStreamParser]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        HasUploaderAccessOrReadOnly
    ]
