# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.files import File
from django.dispatch import receiver
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, CreateModelMixin
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.reverse import reverse
from rest_framework.viewsets import GenericViewSet

from astrobin_apps_images.api import signals
from astrobin_apps_images.api.mixins import TusPatchMixin, TusHeadMixin, TusTerminateMixin, \
    TusCreateMixin
from astrobin_apps_images.api.parsers import TusUploadStreamParser
from astrobin_apps_images.api.permissions import HasUploaderAccessOrReadOnly, IsImageOwnerOrReadOnly
from astrobin_apps_images.api.serializers import UncompressedSourceUploadSerializer
from astrobin_apps_images.api.views.image_view_set import UploadMetadata
from astrobin_apps_images.models import UncompressedSourceUpload
from common.upload_paths import uncompressed_source_upload_path


class UncompressedSourceUploadViewSet(TusCreateMixin,
                                      TusPatchMixin,
                                      TusHeadMixin,
                                      TusTerminateMixin,
                                      CreateModelMixin,
                                      RetrieveModelMixin,
                                      UpdateModelMixin,
                                      GenericViewSet):
    serializer_class = UncompressedSourceUploadSerializer
    queryset = UncompressedSourceUpload.objects.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    metadata_class = UploadMetadata
    parser_classes = [TusUploadStreamParser]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        HasUploaderAccessOrReadOnly,
        IsImageOwnerOrReadOnly
    ]
    http_method_names = ['get', 'post', 'head', 'put', 'patch']

    def get_file_field_name(self):
        return "uncompressed_source_file"

    def get_upload_path_function(self):
        return uncompressed_source_upload_path

    def get_success_headers(self, data):
        try:
            return {
                'Location': reverse(
                    'astrobin_apps_images:uncompressed-source-upload-detail',
                    kwargs={'pk': data['pk']})
            }
        except (TypeError, KeyError):
            return {}

    def verify_file(self, f):
        return True


@receiver(signals.saved)
def uncompresed_source_upload_saved(sender, **kwargs):
    if sender.__class__.__name__ != "UncompressedSourceUpload":
        return

    uploaded_file = sender.uncompressed_source_file
    image = sender.image

    image.uncompressed_source_file = File(uploaded_file, uploaded_file.name)
    image.save()
