from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from pybb.models import Topic
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin.permissions import CustomForumPermissions
from astrobin_apps_forum.api.filters import TopicFilter
from astrobin_apps_forum.api.serializers.topic_serializer import TopicSerializer
from astrobin_apps_forum.services import ForumService
from common.permissions import ReadOnly


class TopicViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    serializer_class = TopicSerializer
    permission_classes = [ReadOnly]
    filter_class = TopicFilter
    http_method_names = ['get', 'head']

    def get_queryset(self) -> QuerySet:
        queryset = Topic.objects.filter(on_moderation=False).select_related('forum', 'user')
        return CustomForumPermissions().filter_topics(self.request.user, queryset)

    @action(detail=False, methods=['get'])
    def latest(self, request) -> Response:
        topics = ForumService.latest_topics(request.user)
        page = self.paginate_queryset(topics)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
