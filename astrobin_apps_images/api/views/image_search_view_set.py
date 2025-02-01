import logging

from django.core.cache import cache
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_haystack.filters import HaystackFilter, HaystackOrderingFilter
from haystack.query import SearchQuerySet
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from astrobin import utils
from astrobin.models import Image
from astrobin_apps_equipment.api.serializers.brand_listing_serializer import BrandListingSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_serializer import \
    EquipmentItemMarketplaceListingLineItemSerializer
from astrobin_apps_equipment.api.serializers.item_listing_serializer import ItemListingSerializer
from astrobin_apps_images.api.serializers import ImageSearchSerializer
from astrobin_apps_premium.services.premium_service import PremiumService
from common.api_page_size_pagination import PageSizePagination
from common.encoded_search_viewset import EncodedSearchViewSet
from common.permissions import ReadOnly
from common.services.search_service import MatchType, SearchService

log = logging.getLogger(__name__)


class ImageSearchViewSet(EncodedSearchViewSet):
    index_models = [Image]
    serializer_class = ImageSearchSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]
    filter_backends = (HaystackFilter, HaystackOrderingFilter)
    ordering_fields = ('published', 'title', 'w', 'h', 'likes')
    ordering = ('-published',)
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'search'
    pagination_class = PageSizePagination

    def list(self, request, *args, **kwargs):
        response = super(ImageSearchViewSet, self).list(request, *args, **kwargs)
        data = response.data

        request_country = utils.get_client_country_code(request)

        text = request.query_params.get('text')
        if text and isinstance(text, list) and len(text) > 0:
            text = text[0]

        telescope = request.query_params.get('telescope')
        if telescope and len(telescope) > 0:
            telescope = telescope.get('value')[0].get('name')

        camera = request.query_params.get('camera')
        if camera and len(camera) > 0:
            camera = camera.get('value')[0].get('name')

        q = telescope or camera or text

        if q and isinstance(q, str) and len(q) > 0:
            item_listings_cache_key = f'equipment_item_listings__{q}__{request_country}'
            brand_listings_cache_key = f'equipment_brand_listings__{q}__{request_country}'
            marketplace_line_items_cache_key = f'marketplace_line_items__{q}'

            equipment_item_listings = cache.get(item_listings_cache_key)
            if equipment_item_listings is None:
                equipment_item_listings = ItemListingSerializer(
                    SearchService.get_equipment_item_listings(q, request_country),
                    many=True
                ).data
                cache.set(item_listings_cache_key, equipment_item_listings, 60 * 60)

            equipment_brand_listings = cache.get(brand_listings_cache_key)
            if equipment_brand_listings is None:
                equipment_brand_listings = BrandListingSerializer(
                    SearchService.get_equipment_brand_listings(q, request_country),
                    many=True
                ).data
                cache.set(brand_listings_cache_key, equipment_brand_listings, 60 * 60)

            marketplace_line_items = cache.get(marketplace_line_items_cache_key)
            if marketplace_line_items is None:
                marketplace_line_items = EquipmentItemMarketplaceListingLineItemSerializer(
                    SearchService.get_marketplace_line_items(q),
                    many=True
                ).data
                cache.set(marketplace_line_items_cache_key, marketplace_line_items, 60 * 60)

            valid_subscription = PremiumService(request.user).get_valid_usersubscription()
            allow_full_retailer_integration = PremiumService.allow_full_retailer_integration(valid_subscription, None)

            additional_info = {
                'equipment_item_listings': equipment_item_listings,
                'equipment_brand_listings': equipment_brand_listings,
                'marketplace_line_items': marketplace_line_items,
                'allow_full_retailer_integration': allow_full_retailer_integration,
            }

            data.update(additional_info)

        return Response(data)

    def filter_images(self, params: dict, queryset: SearchQuerySet) -> SearchQuerySet:
        queryset = queryset.models(Image)
        queryset = SearchService.filter_by_subject(params, queryset)
        queryset = SearchService.filter_by_telescope(params, queryset)
        queryset = SearchService.filter_by_sensor(params, queryset)
        queryset = SearchService.filter_by_camera(params, queryset)
        queryset = SearchService.filter_by_mount(params, queryset)
        queryset = SearchService.filter_by_filter(params, queryset)
        queryset = SearchService.filter_by_accessory(params, queryset)
        queryset = SearchService.filter_by_software(params, queryset)
        # Remove next method after the old search page is gone.
        queryset = SearchService.filter_by_telescope_type(params, queryset)
        queryset = SearchService.filter_by_telescope_types(params, queryset)
        # Remove next method after the old search page is gone.
        queryset = SearchService.filter_by_camera_type(params, queryset)
        queryset = SearchService.filter_by_camera_types(params, queryset)
        queryset = SearchService.filter_by_acquisition_months(params, queryset)
        queryset = SearchService.filter_by_remote_source(params, queryset)
        queryset = SearchService.filter_by_subject_type(params, queryset)
        queryset = SearchService.filter_by_color_or_mono(params, queryset)
        queryset = SearchService.filter_by_modified_camera(params, queryset)
        queryset = SearchService.filter_by_animated(params, queryset)
        queryset = SearchService.filter_by_video(params, queryset)
        queryset = SearchService.filter_by_award(params, queryset)
        queryset = SearchService.filter_by_country(params, queryset)
        queryset = SearchService.filter_by_data_source(params, queryset)
        queryset = SearchService.filter_by_minimum_data(params, queryset)
        queryset = SearchService.filter_by_constellation(params, queryset)
        queryset = SearchService.filter_by_bortle_scale(params, queryset)
        queryset = SearchService.filter_by_license(params, queryset)
        queryset = SearchService.filter_by_camera_pixel_size(params, queryset)
        queryset = SearchService.filter_by_field_radius(params, queryset)
        queryset = SearchService.filter_by_pixel_scale(params, queryset)
        queryset = SearchService.filter_by_telescope_diameter(params, queryset)
        queryset = SearchService.filter_by_telescope_weight(params, queryset)
        queryset = SearchService.filter_by_mount_weight(params, queryset)
        queryset = SearchService.filter_by_mount_max_payload(params, queryset)
        queryset = SearchService.filter_by_telescope_focal_length(params, queryset)
        queryset = SearchService.filter_by_integration_time(params, queryset)
        queryset = SearchService.filter_by_filter_types(params, queryset)
        queryset = SearchService.filter_by_size(params, queryset)
        queryset = SearchService.filter_by_acquisition_type(params, queryset)
        queryset = SearchService.filter_by_date_published(params, queryset)
        queryset = SearchService.filter_by_date_acquired(params, queryset)
        queryset = SearchService.filter_by_moon_phase(params, queryset)
        queryset = SearchService.filter_by_coords(params, queryset)
        queryset = SearchService.filter_by_image_size(params, queryset)
        queryset = SearchService.filter_by_groups(params, self.request.user, queryset)
        queryset = SearchService.filter_by_personal_filters(params, self.request.user, queryset)
        queryset = SearchService.filter_by_equipment_ids(params, queryset)
        queryset = SearchService.filter_by_user_id(params, queryset)
        queryset = SearchService.filter_by_username(params, queryset)
        queryset = SearchService.filter_by_similar_images(params, queryset)
        queryset = SearchService.filter_by_collaboration(params, queryset)

        ordering = params.get('ordering', '-published')

        # Special fixes for some fields.
        if ordering.endswith('field_radius'):
            queryset = queryset.exclude(_missing_='field_radius')
        elif ordering.endswith('pixel_scale'):
            queryset = queryset.exclude(_missing_='pixel_scale')
        elif ordering.endswith('coord_ra_min'):
            queryset = queryset.exclude(_missing_='coord_ra_min')
        elif ordering.endswith('coord_dec_min'):
            queryset = queryset.exclude(_missing_='coord_dec_min')

        if ordering != 'relevance':
            queryset = queryset.order_by(ordering)

        return queryset

    def filter_queryset(self, queryset: SearchQuerySet) -> SearchQuerySet:
        # Preprocess query params to handle boolean fields
        params = self.simplify_one_item_lists(self.request.query_params)
        params = self.preprocess_query_params(params)

        self.request = self.update_request_params(self.request, params)

        text = params.get('text', dict(value=''))
        if isinstance(text, str):
            text = dict(value=text)
            if ' ' in text:
                text['matchType'] = MatchType.ALL.value

        if text.get('value'):
            log.debug(f"Searching for: {text.get('value')}")
            queryset = EncodedSearchViewSet.build_search_query(queryset, text)

        queryset = self.filter_images(params, queryset)

        return queryset
