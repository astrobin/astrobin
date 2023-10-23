# -*- coding: utf-8 -*-

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_image_serializer import \
    EquipmentItemMarketplaceListingLineItemImageSerializer
from common.permissions import IsObjectUserOrReadOnly


class EquipmentItemMarketplaceListingLineItemImageViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsObjectUserOrReadOnly
    ]
    serializer_class = EquipmentItemMarketplaceListingLineItemImageSerializer
    http_method_names = ['get', 'head', 'post']

    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.all()
