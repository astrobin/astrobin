import logging

from django.contrib.auth.models import User
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_haystack.filters import HaystackFilter, HaystackOrderingFilter
from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_users.api.serializers.user_search_serializer import UserSearchSerializer
from common.api_page_size_pagination import PageSizePagination
from common.encoded_search_viewset import EncodedSearchViewSet
from common.permissions import ReadOnly
from common.services.search_service import MatchType

log = logging.getLogger(__name__)


class UserSearchViewSet(EncodedSearchViewSet):
    index_models = [User]
    serializer_class = UserSearchSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]
    filter_backends = (HaystackFilter, HaystackOrderingFilter)
    ordering_fields = (
        '_score', 
        'username', 
        'display_name',
        'avatar_url',
        'images',
        'total_likes_received',
        'followers',
        'contribution_index',
        'normalized_likes',
        'integration',
        'top_pick_nominations',
        'top_picks',
        'iotds',
        'comments_written',
        'comments_received',  # Updated to match serializer field name
        'comment_likes_received',
        'forum_posts',
        'forum_post_likes_received'
    )
    ordering = ('-_score',)
    pagination_class = PageSizePagination

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
            # Instead of creating a new queryset, we filter the existing one
            queryset = queryset.filter(display_name=AutoQuery(text.get('value')))

        # Check if ordering parameter exists in the params and apply it explicitly
        ordering = params.get('ordering')
        if ordering:
            log.debug(f"Explicitly ordering by: {ordering}")
            order_direction = ''
            order_field = ordering
            
            # Check if it's a descending order (starts with minus)
            if ordering.startswith('-'):
                order_direction = '-'
                order_field = ordering[1:]  # Remove the minus sign
            
            # Special case for comments_received which maps to comments in the index
            if order_field == 'comments_received':
                order_field = 'comments'
                
            # Apply the ordering to the queryset
            if order_field in self.ordering_fields or order_field == 'comments':
                queryset = queryset.order_by(f"{order_direction}{order_field}")
            else:
                log.warning(f"Ordering field '{order_field}' not in allowed ordering_fields")

        return queryset
