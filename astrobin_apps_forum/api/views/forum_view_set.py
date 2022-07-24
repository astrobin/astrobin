from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from pybb.models import Forum
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.permissions import CustomForumPermissions
from astrobin_apps_forum.api.filters.forum_filter import ForumFilter
from astrobin_apps_forum.api.serializers.forum_serializer import ForumSerializer
from common.permissions import ReadOnly


class ForumViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    serializer_class = ForumSerializer
    permission_classes = [ReadOnly]
    filter_class = ForumFilter
    http_method_names = ['get', 'head']

    def get_queryset(self) -> QuerySet:
        queryset = Forum.objects.filter(hidden=False)
        return CustomForumPermissions().filter_forums(self.request.user, queryset)
