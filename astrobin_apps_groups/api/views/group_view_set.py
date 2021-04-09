from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_groups.api.filters.group_filter import GroupFilter
from astrobin_apps_groups.api.permissions import IsOwnerOrReadOnly
from astrobin_apps_groups.api.serializers.group_serializer import GroupSerializer
from astrobin_apps_groups.models import Group


class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    filter_class = GroupFilter
    permissions = [IsOwnerOrReadOnly]
    http_method_names = ['get', 'post', 'head', 'put', 'patch', 'delete']
