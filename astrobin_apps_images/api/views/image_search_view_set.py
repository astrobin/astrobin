from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_haystack.filters import HaystackFilter, HaystackOrderingFilter
from haystack.query import SearchQuerySet
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.throttling import ScopedRateThrottle

from astrobin.models import Image
from astrobin_apps_images.api.serializers import ImageSearchSerializer
from common.api_page_size_pagination import PageSizePagination
from common.encoded_search_viewset import EncodedSearchViewSet
from common.permissions import ReadOnly
from common.services.search_service import SearchService


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

    def filter_images(self, params: dict, queryset: SearchQuerySet) -> SearchQuerySet:
        queryset = queryset.models(Image)
        queryset = SearchService.filter_by_subject(params, queryset)
        queryset = SearchService.filter_by_telescope(params, queryset)
        queryset = SearchService.filter_by_camera(params, queryset)
        queryset = SearchService.filter_by_telescope_type(params, queryset)
        queryset = SearchService.filter_by_camera_type(params, queryset)
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

        text = params.get('text', '')

        if text:
            queryset = queryset.auto_query(text)
        queryset = self.filter_images(params, queryset)

        return queryset
