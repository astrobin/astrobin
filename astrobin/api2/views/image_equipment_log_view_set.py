from django_filters.rest_framework import DjangoFilterBackend
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.api2.serializers.image_equipment_log_serializer import ImageEquipmentLogSerializer
from astrobin.models import ImageEquipmentLog
from common.api_page_size_pagination import PageSizePagination
from common.permissions import ReadOnly


class ImageEquipmentLogViewSet(viewsets.ModelViewSet):
    queryset = ImageEquipmentLog.objects.all().order_by('date')
    serializer_class = ImageEquipmentLogSerializer
    permission_classes = (ReadOnly,)
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('verb', 'image__user', 'equipment_item_content_type', 'equipment_item_object_id')
    pagination_class = PageSizePagination
