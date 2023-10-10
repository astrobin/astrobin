# -*- coding: utf-8 -*-

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_image_upload_serializer import \
    EquipmentItemMarketplaceListingImageUploadSerializer
from astrobin_apps_images.api.mixins import TusCreateMixin, TusHeadMixin, TusPatchMixin, TusTerminateMixin
from astrobin_apps_images.api.parsers import TusUploadStreamParser
from astrobin_apps_images.api.views.image_upload_view_set import UploadMetadata
from astrobin_apps_images.services import ImageService
from common.permissions import IsObjectUserOrReadOnly
from common.upload_paths import marketplace_listing_upload_path


class EquipmentItemMarketplaceListingImageUploadViewSet(
    TusCreateMixin,
    TusPatchMixin,
    TusHeadMixin,
    TusTerminateMixin,
    viewsets.ModelViewSet
):
    metadata_class = UploadMetadata
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [TusUploadStreamParser]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsObjectUserOrReadOnly
    ]
    serializer_class = EquipmentItemMarketplaceListingImageUploadSerializer
    http_method_names = ['get', 'head', 'post', 'patch']

    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.all()

    def get_file_field_name(self, mime_type: str) -> str:
        return 'image_file'

    def get_upload_path_function(self, mime_type: str):
        return marketplace_listing_upload_path

    def verify_file(self, file_path: str, mime_type: str) -> bool:
        return ImageService.is_image(file_path)

    def get_success_headers(self, data):
        return {'Location': '.'}
