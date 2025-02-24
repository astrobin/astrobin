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
    ordering_fields = ('_score', 'username', 'date_joined', 'last_login')
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
            queryset = SearchQuerySet().models(User).filter(display_name=AutoQuery(text.get('value')))

        return queryset
