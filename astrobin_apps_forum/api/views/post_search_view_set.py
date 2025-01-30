from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_haystack.filters import HaystackFilter
from haystack.query import SearchQuerySet
from pybb.models import Post
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.throttling import ScopedRateThrottle

from astrobin_apps_forum.api.serializers.post_search_serializer import PostSearchSerializer
from common.api_page_size_pagination import PageSizePagination
from common.encoded_search_viewset import EncodedSearchViewSet
from common.permissions import ReadOnly
from common.services.search_service import MatchType, SearchService


class PostSearchViewSet(EncodedSearchViewSet):
    index_models = [Post]
    serializer_class = PostSearchSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]
    filter_backends = (HaystackFilter,)
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'search'
    pagination_class = PageSizePagination

    def filter_posts(self, params: dict, queryset: SearchQuerySet) -> SearchQuerySet:
        queryset = SearchService.filter_by_forum_topic(params, queryset)
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
            queryset = EncodedSearchViewSet.build_search_query(queryset, text)

        queryset = self.filter_posts(params, queryset)

        queryset = queryset.order_by('-created')

        return queryset
