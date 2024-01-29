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

        if self.request.GET.get('max_distance') and \
                self.request.GET.get('distance_unit') and \
                self.request.GET.get('latitude') and \
                self.request.GET.get('longitude'):
            max_distance = float(self.request.GET.get('max_distance'))
            distance_unit = self.request.GET.get('distance_unit')
            latitude = float(self.request.GET.get('latitude'))
            longitude = float(self.request.GET.get('longitude'))

            if distance_unit == 'mi':
                max_distance *= 1.60934  # Convert miles to kilometers

            max_distance *= 1000  # Convert kilometers to meters

            qs = qs.extra(
                where=[
                    "earth_box(ll_to_earth(%s, %s), %s) @> ll_to_earth(latitude, longitude)",
                    "earth_distance(ll_to_earth(%s, %s), ll_to_earth(latitude, longitude)) <= %s"
                ],
                params=[latitude, longitude, max_distance, latitude, longitude, max_distance]
            )

        return qs

    def get_serializer_class(self) -> Type[serializers.ModelSerializer]:
        if self.request.method in ['PUT', 'POST']:
            return EquipmentItemMarketplaceListingSerializer

        return EquipmentItemMarketplaceListingReadSerializer
