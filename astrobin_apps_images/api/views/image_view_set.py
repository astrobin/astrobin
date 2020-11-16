# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.metadata import BaseMetadata
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.reverse import reverse

from astrobin.models import Image
from astrobin_apps_images.api.constants import TUS_API_VERSION, TUS_API_EXTENSIONS, TUS_MAX_FILE_SIZE, \
    TUS_API_CHECKSUM_ALGORITHMS
from astrobin_apps_images.api.filters import ImageFilter
from astrobin_apps_images.api.mixins import TusPatchMixin, TusHeadMixin, TusTerminateMixin, \
    TusCreateMixin
from astrobin_apps_images.api.parsers import TusUploadStreamParser
from astrobin_apps_images.api.serializers import ImageSerializer
from common.upload_paths import image_upload_path


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
    ]

    def get_file_field_name(self):
        return "image_file"

    def get_upload_path_function(self):
        return image_upload_path

    def get_object_serializer(self, request, filename, upload_length, upload_metadata):
        try:
            width = int(upload_metadata['width'])
            height = int(upload_metadata['height'])
        except (KeyError, ValueError):
            width = 0
            height = 0

        return self.get_serializer(data={
            'upload_length': upload_length,
            'upload_metadata': json.dumps(upload_metadata),
            'filename': filename,
            'title': upload_metadata['title'],
            'is_wip': True,
            'skip_notifications': False,
            'user_id': request.user.id,
            'w': width,
            'h': height,
        })

    def get_success_headers(self, data):
        try:
            return {'Location': reverse('astrobin_apps_images:image-detail', kwargs={'pk': data['pk']})}
        except (TypeError, KeyError):
            return {}
