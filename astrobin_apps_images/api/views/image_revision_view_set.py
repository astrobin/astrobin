# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.reverse import reverse

from astrobin.models import ImageRevision, Image
from astrobin_apps_images.api.filters import ImageRevisionFilter
from astrobin_apps_images.api.mixins import TusPatchMixin, TusHeadMixin, TusTerminateMixin, \
    TusCreateMixin
from astrobin_apps_images.api.parsers import TusUploadStreamParser
from astrobin_apps_images.api.permissions import HasUploaderAccessOrReadOnly, IsImageOwnerOrReadOnly
from astrobin_apps_images.api.serializers import ImageRevisionSerializer
from astrobin_apps_images.api.views.image_view_set import UploadMetadata
from astrobin_apps_images.services import ImageService
from common.upload_paths import image_upload_path


class ImageRevisionViewSet(TusCreateMixin,
                           TusPatchMixin,
                           TusHeadMixin,
                           TusTerminateMixin,
                           viewsets.ModelViewSet):
    serializer_class = ImageRevisionSerializer
    queryset = ImageRevision.objects.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    filter_class = ImageRevisionFilter
    metadata_class = UploadMetadata
    parser_classes = [TusUploadStreamParser]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        HasUploaderAccessOrReadOnly,
        IsImageOwnerOrReadOnly
    ]

    def get_file_field_name(self):
        return "image_file"

    def get_upload_path_function(self):
        return image_upload_path

    def get_object_serializer(self, request, filename, upload_length, upload_metadata):
        image_id = upload_metadata['image_id']
        image = Image.objects_including_wip.get(pk=image_id)

        return self.get_serializer(data={
            'upload_length': upload_length,
            'upload_metadata': json.dumps(upload_metadata),
            'filename': filename,
            'description': upload_metadata['description'] if upload_metadata['description'] != 'NO_VALUE' else '',
            'skip_notifications': upload_metadata[
                'skip_notifications'] if 'skip_notifications' in upload_metadata else False,
            'is_final': upload_metadata[
                'mark_as_final'] if 'mark_as_final' in upload_metadata else False,
            'image': upload_metadata['image_id'],
            'label': ImageService(image).get_next_available_revision_label(),
        })


    def get_success_headers(self, data):
        try:
            return {'Location': reverse('astrobin_apps_images:image-revision-detail', kwargs={'pk': data['pk']})}
        except (TypeError, KeyError):
            return {}
