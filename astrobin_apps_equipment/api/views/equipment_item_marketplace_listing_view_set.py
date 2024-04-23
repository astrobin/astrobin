from typing import Type

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import TrigramDistance
from django.db.models import OuterRef, Prefetch, Q, QuerySet
from django.utils.translation import gettext
from django_filters.rest_framework import DjangoFilterBackend
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import serializers, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import Request
from rest_framework.response import Response

from astrobin.settings.components.payments import SUPPORTED_CURRENCIES
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_read_serializer import \
    EquipmentItemMarketplaceListingReadSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_serializer import \
    EquipmentItemMarketplaceListingSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_equipment.types.marketplace_line_item_condition import MarketplaceLineItemCondition
from astrobin_apps_payments.models import ExchangeRate
from common.permissions import IsObjectUserOrReadOnly
from common.services import DateTimeService
from toggleproperties.models import ToggleProperty


class EquipmentItemMarketplaceListingViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('hash', 'user')

    def get_queryset(self) -> QuerySet:
        self.validate_query_params()
        queryset = EquipmentItemMarketplaceListing.objects.all()
        queryset = self.filter_by_excluded_hash(queryset)
        queryset = self.filter_by_expiration(queryset)
        queryset = self.filter_by_distance(queryset)
        queryset = self.filter_by_region(queryset)

        line_items_queryset = EquipmentItemMarketplaceListingLineItem.objects.all()
        line_items_queryset = self.filter_line_items(line_items_queryset)

        return queryset.prefetch_related(Prefetch('line_items', queryset=line_items_queryset))

    def filter_by_excluded_hash(self, queryset: QuerySet) -> QuerySet:
        hash_param = self.request.query_params.get('exclude_listing')
        if hash_param:
            queryset = queryset.exclude(hash=hash_param)
        return queryset

    def filter_by_expiration(self, queryset: QuerySet) -> QuerySet:
        now = DateTimeService.now()
        get_expired = self.request.query_params.get('expired', 'false') == 'true'
        hash_param = self.request.query_params.get('hash')

        if get_expired and self.request.user.is_authenticated:
            queryset = queryset.filter(Q(expiration__lt=now, user=self.request.user) | Q(expiration__gte=now))
        elif get_expired:
            queryset = EquipmentItemMarketplaceListing.objects.none()
        else:
            queryset = queryset.filter(expiration__gte=now)

        if hash_param:
            queryset = queryset.filter(hash=hash_param)
            if self.request.user.is_authenticated:
                # Allow fetching of own expired listing by hash
                queryset = queryset | EquipmentItemMarketplaceListing.objects.filter(
                    hash=hash_param, user=self.request.user
                )

        return queryset

    def filter_by_distance(self, queryset: QuerySet) -> QuerySet:
        max_distance = self.request.GET.get('max_distance')
        distance_unit = self.request.GET.get('distance_unit')
        latitude = self.request.GET.get('latitude')
        longitude = self.request.GET.get('longitude')

        if max_distance and distance_unit and latitude and longitude:
            max_distance = float(max_distance)
            latitude = float(latitude)
            longitude = float(longitude)

            if distance_unit == 'mi':
                max_distance *= 1.60934  # Convert miles to kilometers
            max_distance *= 1000  # Convert kilometers to meters

            return queryset.extra(
                where=[
                    "earth_box(ll_to_earth(%s, %s), %s) @> ll_to_earth(latitude, longitude)",
                    "earth_distance(ll_to_earth(%s, %s), ll_to_earth(latitude, longitude)) <= %s"
                ],
                params=[latitude, longitude, max_distance, latitude, longitude, max_distance]
            )
        return queryset

    def filter_by_region(self, queryset: QuerySet) -> QuerySet:
        region = self.request.GET.get('region')
        if region:
            return queryset.filter(country=region.upper())
        return queryset

    def filter_line_items(self, queryset: QuerySet) -> QuerySet:
        queryset = self.filter_line_items_with_offers_by_user(queryset)
        queryset = self.filter_line_items_sold_to_user(queryset)
        queryset = self.filter_line_items_followed_by_user(queryset)
        queryset = self.filter_line_items_by_sold_status(queryset)
        queryset = self.filter_line_items_by_item_type(queryset)
        queryset = self.filter_line_items_by_price(queryset)
        queryset = self.filter_line_items_by_condition(queryset)
        queryset = self.filter_line_items_by_query(queryset)
        return queryset

    def filter_line_items_with_offers_by_user(self, queryset: QuerySet) -> QuerySet:
        try:
            user_id = int(self.request.query_params.get('offers_by_user'))
        except (ValueError, TypeError):
            return queryset

        if self.request.user.is_authenticated and user_id == self.request.user.id:
            return queryset.filter(offers__user_id=user_id)

        return queryset

    def filter_line_items_sold_to_user(self, queryset: QuerySet) -> QuerySet:
        try:
            user_id = int(self.request.query_params.get('sold_to_user'))
        except (ValueError, TypeError):
            return queryset

        if self.request.user.is_authenticated and user_id == self.request.user.id:
            return queryset.filter(sold_to=user_id)

        return queryset

    def filter_line_items_followed_by_user(self, queryset: QuerySet) -> QuerySet:
        try:
            user_id = int(self.request.query_params.get('followed_by_user'))
        except (ValueError, TypeError):
            return queryset

        if self.request.user.is_authenticated and user_id == self.request.user.id:
            followed_item_ids = ToggleProperty.objects.filter(
                user=self.request.user,
                content_type=ContentType.objects.get_for_model(EquipmentItemMarketplaceListing),
                object_id=OuterRef('pk'),
                property_type='follow'
            ).values_list('object_id', flat=True)

            return queryset.filter(pk__in=followed_item_ids)

        return queryset

    def filter_line_items_by_sold_status(self, queryset: QuerySet) -> QuerySet:
        sold = self.request.query_params.get('sold')

        if sold is None:
            return queryset

        if sold == 'true':
            return queryset.filter(sold__isnull=False)

        return queryset.filter(sold__isnull=True)

    def filter_line_items_by_item_type(self, queryset: QuerySet) -> QuerySet:
        item_type = self.request.query_params.get('item_type')
        if item_type:
            content_type = EquipmentService.item_type_to_content_type(item_type)
            if content_type:
                return queryset.filter(item_content_type=content_type)
        return queryset

    def filter_line_items_by_price(self, queryset: QuerySet) -> QuerySet:
        currency = self.request.query_params.get('currency')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if currency and currency not in SUPPORTED_CURRENCIES:
            raise ValidationError({'currency': gettext('Currency not supported.')})

        exchange_rate = None
        if currency:
            exchange_rate = ExchangeRate.objects.filter(source='CHF', target=currency).first()
            if exchange_rate is None:
                raise ValidationError({'currency': gettext('AstroBin couldn\'t fetch an exchange rate for the selected currency.')})

        if min_price and currency:
            min_price = float(min_price)
            if currency != 'CHF' and exchange_rate and exchange_rate.rate:
                min_price /= float(exchange_rate.rate)
            queryset = queryset.filter(price_chf__gte=min_price)

        if max_price and currency:
            max_price = float(max_price)
            if currency != 'CHF' and exchange_rate and exchange_rate.rate:
                max_price /= float(exchange_rate.rate)
            queryset = queryset.filter(price_chf__lte=max_price)

        return queryset

    def filter_line_items_by_condition(self, queryset: QuerySet) -> QuerySet:
        condition = self.request.query_params.get('condition')
        if condition and condition not in (item.value for item in MarketplaceLineItemCondition):
            raise ValidationError({'condition': gettext('Invalid condition.')})
        return queryset.filter(condition=condition) if condition else queryset

    def filter_line_items_by_query(self, queryset: QuerySet) -> QuerySet:
        query = self.request.query_params.get('query')
        if query:
            if 'postgres' in settings.DATABASES['default']['ENGINE']:
                queryset = queryset.annotate(
                    distance=TrigramDistance('item_name', query),
                ).filter(
                    Q(item_name__icontains=query) |
                    Q(distance__lte=.8)
                ).order_by(
                    'distance'
                )
            else:
                queryset = queryset.filter(item_name__icontains=query)

        return queryset

    def retrieve(self, request: Request, *args: object, **kwargs: object) -> object:
        try:
            instance = EquipmentItemMarketplaceListing.objects.get(pk=kwargs['pk'])
        except EquipmentItemMarketplaceListing.DoesNotExist:
            raise NotFound()

        if instance.expiration < DateTimeService.now() and instance.user != request.user:
            raise NotFound()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_destroy(self, serializer):
        instance = serializer.instance

        if instance.line_items.filter(sold__isnull=False).exists():
            raise serializers.ValidationError("Cannot delete a listing that has sold line items")

        super().perform_destroy(serializer)

    def get_serializer_class(self) -> Type[serializers.ModelSerializer]:
        if self.request.method in ['PUT', 'POST']:
            return EquipmentItemMarketplaceListingSerializer

        return EquipmentItemMarketplaceListingReadSerializer

    def validate_query_params(self):
        allowed_params = [
            'page',
            'expired',
            'max_distance',
            'distance_unit',
            'latitude',
            'longitude',
            'region',
            'offers_by_user',
            'sold_to_user',
            'followed_by_user',
            'sold',
            'item_type',
            'currency',
            'min_price',
            'max_price',
            'condition',
            'query',
            'user',
            'hash',
            'exclude_listing',
        ]

        for param in self.request.query_params:
            if param not in allowed_params:
                raise ValidationError({'detail': f'Invalid query parameter: {param}'})
