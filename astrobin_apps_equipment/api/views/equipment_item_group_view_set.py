from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_group_serializer import EquipmentItemGroupSerializer
from astrobin_apps_equipment.models import EquipmentItemGroup
from common.permissions import ReadOnly


class EquipmentItemGroupViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [ReadOnly]
    http_method_names = ['get', 'head', 'options']
    serializer_class = EquipmentItemGroupSerializer
    queryset = EquipmentItemGroup.objects.all()
