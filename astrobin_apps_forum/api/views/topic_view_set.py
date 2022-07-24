from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from pybb.models import Topic
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.permissions import CustomForumPermissions
from astrobin_apps_forum.api.filters import TopicFilter
from astrobin_apps_forum.api.serializers.topic_serializer import TopicSerializer
from common.permissions import ReadOnly


class TopicViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    serializer_class = TopicSerializer
    permission_classes = [ReadOnly]
    filter_class = TopicFilter
    http_method_names = ['get', 'head']

    def get_queryset(self) -> QuerySet:
        queryset = Topic.objects.filter(on_moderation=False)
        return CustomForumPermissions().filter_topics(self.request.user, queryset)
