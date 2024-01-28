from typing import Type

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import serializers, viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_read_serializer import \
    EquipmentItemMarketplaceListingReadSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_serializer import \
    EquipmentItemMarketplaceListingSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing
from astrobin_apps_equipment.services import EquipmentService
from common.permissions import IsObjectUserOrReadOnly


class EquipmentItemMarketplaceListingViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('hash', 'user')

    def get_queryset(self) -> QuerySet:
        qs = EquipmentItemMarketplaceListing.objects.all()

        if self.request.GET.get('item_type'):
            item_type = self.request.GET.get('item_type')
            content_type = EquipmentService.item_type_to_content_type(item_type)
            if content_type:
                qs = qs.filter(line_items__item_content_type=content_type)

        return qs


    def get_serializer_class(self) -> Type[serializers.ModelSerializer]:
        if self.request.method in ['PUT', 'POST']:
            return EquipmentItemMarketplaceListingSerializer

        return EquipmentItemMarketplaceListingReadSerializer
