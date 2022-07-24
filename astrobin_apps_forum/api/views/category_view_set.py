from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from pybb.models import Category
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_forum.api.filters import CategoryFilter
from astrobin_apps_forum.api.serializers import CategorySerializer
from common.permissions import ReadOnly


class CategoryViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    serializer_class = CategorySerializer
    permission_classes = [ReadOnly]
    filter_class = CategoryFilter
    http_method_names = ['get', 'head']
    queryset = Category.objects.filter(hidden=False)
