from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_read_only import IsEquipmentModeratorOrReadOnly


class EquipmentItemViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [IsEquipmentModeratorOrReadOnly]
    http_method_names = ['get', 'post', 'head', 'put', 'patch']

    class Meta:
        abstract = True
