from typing import Type

from django.db.models import Prefetch, QuerySet
from django.utils.translation import gettext
from django_filters.rest_framework import DjangoFilterBackend
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.settings.components.payments import SUPPORTED_CURRENCIES
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_read_serializer import \
    EquipmentItemMarketplaceListingReadSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_serializer import \
    EquipmentItemMarketplaceListingSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_payments.models import ExchangeRate
from common.permissions import IsObjectUserOrReadOnly


class EquipmentItemMarketplaceListingViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('hash', 'user')

    def get_queryset(self) -> QuerySet:
        line_items_queryset = self.filter_line_items(
            EquipmentItemMarketplaceListingLineItem.objects.all()
        )

        queryset = self.filter_listings(
            EquipmentItemMarketplaceListing.objects.all()
        ).prefetch_related(
            Prefetch('line_items', queryset=line_items_queryset)
        )

        return queryset

    def filter_listings(self, queryset: QuerySet) -> QuerySet:
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

            queryset = queryset.extra(
                where=[
                    "earth_box(ll_to_earth(%s, %s), %s) @> ll_to_earth(latitude, longitude)",
                    "earth_distance(ll_to_earth(%s, %s), ll_to_earth(latitude, longitude)) <= %s"
                ],
                params=[latitude, longitude, max_distance, latitude, longitude, max_distance]
            )

        return queryset

    def filter_line_items(self, queryset: QuerySet) -> QuerySet:
        if self.request.GET.get('item_type'):
            item_type = self.request.GET.get('item_type')
            content_type = EquipmentService.item_type_to_content_type(item_type)
            if content_type:
                queryset = queryset.filter(item_content_type=content_type)

        if self.request.GET.get('currency'):
            currency = self.request.GET.get('currency')
            if currency not in SUPPORTED_CURRENCIES:
                raise ValidationError(
                    {
                        'currency': gettext('Currency not supported.')
                    }
                )
            exchange_rate = ExchangeRate.objects.filter(source='CHF', target=currency).first()
            if exchange_rate is None:
                raise ValidationError(
                    {
                        'currency': gettext('AstroBin couldn\'t fetch an exchange rate for the selected currency.')
                    }
                )
        else:
            currency = None
            exchange_rate = None

        if self.request.GET.get('min_price') and currency:
            min_price = float(self.request.GET.get('min_price'))
            if currency != 'CHF':
                if exchange_rate and exchange_rate.rate:
                    min_price /= float(exchange_rate.rate)
            queryset = queryset.filter(price_chf__gte=min_price)
            
        if self.request.GET.get('max_price') and currency:
            max_price = float(self.request.GET.get('max_price'))
            if currency != 'CHF':
                if exchange_rate and exchange_rate.rate:
                    max_price /= float(exchange_rate.rate)
            queryset = queryset.filter(price_chf__lte=max_price)

        return queryset

    def get_serializer_class(self) -> Type[serializers.ModelSerializer]:
        if self.request.method in ['PUT', 'POST']:
            return EquipmentItemMarketplaceListingSerializer

        return EquipmentItemMarketplaceListingReadSerializer
