from typing import Type

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import TrigramDistance
from django.db.models import Exists, OuterRef, Prefetch, Q, QuerySet
from django.utils.translation import gettext
from django_filters.rest_framework import DjangoFilterBackend
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import Request
from rest_framework.response import Response

from astrobin.settings.components.payments import SUPPORTED_CURRENCIES
from astrobin_apps_equipment.api.permissions.may_access_marketplace import MayAccessMarketplace
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_read_serializer import \
    EquipmentItemMarketplaceListingReadSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_serializer import \
    EquipmentItemMarketplaceListingSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_equipment.services.marketplace_service import MarketplaceService
from astrobin_apps_equipment.types.marketplace_line_item_condition import MarketplaceLineItemCondition
from astrobin_apps_payments.models import ExchangeRate
from astrobin_apps_premium.services.premium_service import SubscriptionName
from astrobin_apps_users.services import UserService
from common.constants import GroupName
from common.permissions import IsObjectUser, ReadOnly, is_group_member, or_permission, subscription_required
from common.services import DateTimeService
from common.services.caching_service import CachingService
from toggleproperties.models import ToggleProperty


class EquipmentItemMarketplaceListingViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('hash', 'user')

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            permission_classes = [
                MayAccessMarketplace
            ]
        elif self.action == 'create':
            permission_classes = [
                MayAccessMarketplace,
                subscription_required([subscription.value for subscription in SubscriptionName])
            ]
        elif self.action in ('update', 'partial_update', 'destroy'):
            permission_classes = [
                MayAccessMarketplace,
                or_permission(IsObjectUser, is_group_member(GroupName.MARKETPLACE_MODERATORS)),
            ]
        elif self.action == 'approve':
            permission_classes = [
                is_group_member(GroupName.MARKETPLACE_MODERATORS)
            ]
        elif self.action == 'renew':
            permission_classes = [
                MayAccessMarketplace,
                IsObjectUser
            ]
        else:
            permission_classes = [
                IsAdminUser
            ]

        return [permission() for permission in permission_classes]

    def get_queryset(self) -> QuerySet:
        self.validate_query_params()
        queryset = EquipmentItemMarketplaceListing.objects.all()
        queryset = self.filter_approved(queryset)
        queryset = self.filter_by_excluded_hash(queryset)
        queryset = self.filter_by_expiration(queryset)
        queryset = self.filter_by_distance(queryset)
        queryset = self.filter_by_region(queryset)
        queryset = self.filter_by_item_id_and_content_type(queryset)

        line_items_queryset = EquipmentItemMarketplaceListingLineItem.objects.all()
        line_items_queryset = self.filter_line_items(line_items_queryset).distinct()

        return queryset.prefetch_related(Prefetch('line_items', queryset=line_items_queryset)).distinct()

    def filter_approved(self, queryset: QuerySet) -> QuerySet:
        if not self.request.user.is_authenticated:
            return queryset.filter(approved__isnull=False)

        if UserService(self.request.user).is_in_group(GroupName.MARKETPLACE_MODERATORS):
            return queryset

        return queryset.filter(Q(approved__isnull=False) | Q(user=self.request.user))

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
                # Allow fetching by hash if you're the seller or the buyer, or someone with an offer
                queryset = queryset | EquipmentItemMarketplaceListing.objects.filter(
                    Q(hash=hash_param) &
                    Q(
                        Q(line_items__sold_to=self.request.user) |
                        Q(line_items__reserved_to=self.request.user) |
                        Q(offers__user=self.request.user) |
                        Q(user=self.request.user)
                    )
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
        if region and region != 'WORLDWIDE':
            return queryset.filter(country=region.upper())
        return queryset

    def filter_by_item_id_and_content_type(self, queryset: QuerySet) -> QuerySet:
        item_id = self.request.GET.get('item_id')
        content_type_id = self.request.GET.get('content_type_id')

        if item_id and content_type_id:
            content_type = ContentType.objects.get_for_id(content_type_id)
            return queryset.filter(line_items__item_object_id=item_id, line_items__item_content_type=content_type)

        return queryset

    def filter_line_items(self, queryset: QuerySet) -> QuerySet:
        queryset = self.filter_line_items_with_offers_by_user(queryset)
        queryset = self.filter_line_items_sold_to_user(queryset)
        queryset = self.filter_line_items_followed_by_user(queryset)
        queryset = self.filter_line_items_by_pending_moderation_status(queryset)
        queryset = self.filter_line_items_by_sold_status(queryset)
        queryset = self.filter_line_items_by_item_type(queryset)
        queryset = self.filter_line_items_by_price(queryset)
        queryset = self.filter_line_items_by_condition(queryset)
        queryset = self.filter_line_items_by_query(queryset)
        queryset = self.filter_line_items_by_item_id_and_content_type(queryset)
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

    def filter_line_items_followed_by_user(self, queryset):
        try:
            user_id = int(self.request.query_params.get('followed_by_user'))
        except (ValueError, TypeError):
            return queryset

        if self.request.user.is_authenticated and user_id == self.request.user.id:
            content_type = ContentType.objects.get_for_model(EquipmentItemMarketplaceListing)
            followed_item_exists = ToggleProperty.objects.filter(
                user=self.request.user,
                content_type=content_type,
                object_id=OuterRef('pk'),
                property_type='follow'
            )

            return queryset.annotate(follow_exists=Exists(followed_item_exists)).filter(follow_exists=True)

        return queryset

    def filter_line_items_by_pending_moderation_status(self, queryset: QuerySet) -> QuerySet:
        pending_moderation = self.request.query_params.get('pending_moderation')

        if pending_moderation is None:
            return queryset

        if pending_moderation == 'true':
            return queryset.filter(listing__approved__isnull=True)

        return queryset.filter(listing__approved__isnull=False)

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
                    item_name_distance=TrigramDistance('item_name', query),
                    title_distance=TrigramDistance('listing__title', query)
                ).filter(
                    Q(item_name__icontains=query) |
                    Q(item_name_distance__lte=.8) |
                    Q(listing__title__icontains=query) |
                    Q(title_distance__lte=.8)
                ).order_by(
                    'item_name_distance',
                    'title_distance'
                )
            else:
                queryset = queryset.filter(Q(item_name__icontains=query) | Q(listing__title__icontains=query))

        return queryset

    def filter_line_items_by_item_id_and_content_type(self, queryset: QuerySet) -> QuerySet:
        item_id = self.request.GET.get('item_id')
        content_type_id = self.request.GET.get('content_type_id')

        if item_id and content_type_id:
            content_type = ContentType.objects.get_for_id(content_type_id)
            return queryset.filter(item_object_id=item_id, item_content_type=content_type)

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

    def perform_create(self, serializer):
        super().perform_create(serializer)

        MarketplaceService.log_event(
            self.request.user,
            'created',
            self.get_serializer_class(),
            serializer.instance,
            context={'request': self.request},
        )

    def perform_update(self, serializer):
        user = self.request.user

        # get instance
        instance = serializer.instance

        if instance.line_items.filter(sold__isnull=False).exists():
            raise serializers.ValidationError("Cannot edit a listing that has sold line items")

        if instance.line_items.filter(reserved__isnull=False).exists():
            raise serializers.ValidationError("Cannot edit a listing that has reserved line items")

        # get caching service
        caching_service = CachingService()

        # in the caching service, set the user who is updating this instance
        caching_service.set_in_request_cache(f'user_updating_marketplace_instance_{instance.pk}', user)

        # perform the update
        super().perform_update(serializer)

        MarketplaceService.log_event(
            user,
            'updated',
            self.get_serializer_class(),
            instance,
            context={'request': self.request},
        )

    def perform_destroy(self, instance):
        if instance.line_items.filter(sold__isnull=False).exists():
            raise serializers.ValidationError("Cannot delete a listing that has sold line items")

        if instance.line_items.filter(reserved__isnull=False).exists():
            raise serializers.ValidationError("Cannot delete a listing that has reserved line items")

        super().perform_destroy(instance)

        MarketplaceService.log_event(
            self.request.user,
            'deleted',
            self.get_serializer_class(),
            instance,
            context={'request': self.request},
        )

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
            'pending_moderation',
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
            'item_id',
            'content_type_id',
        ]

        for param in self.request.query_params:
            if param not in allowed_params:
                raise ValidationError({'detail': f'Invalid query parameter: {param}'})

    @action(detail=True, methods=['put'])
    def approve(self, request: Request, pk: int) -> Response:
        listing = self.get_object()
        MarketplaceService.approve_listing(listing, request.user)
        listing.refresh_from_db()
        serializer = self.get_serializer(listing)

        MarketplaceService.log_event(
            request.user,
            'approved',
            self.get_serializer_class(),
            listing,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def renew(self, request: Request, pk: int) -> Response:
        try:
            listing = EquipmentItemMarketplaceListing.objects.get(pk=pk)
        except EquipmentItemMarketplaceListing.DoesNotExist:
            raise NotFound()
        MarketplaceService.renew_listing(listing, request.user)
        listing.refresh_from_db()
        serializer = self.get_serializer(listing)

        MarketplaceService.log_event(
            request.user,
            'renewed',
            self.get_serializer_class(),
            listing,
            context={'request': request},
        )

        return Response(serializer.data)
