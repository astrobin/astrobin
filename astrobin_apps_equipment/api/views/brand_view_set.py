from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.filters.equipment_brand_filter import EquipmentBrandFilter
from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_read_only import IsEquipmentModeratorOrReadOnly
from astrobin_apps_equipment.api.serializers.brand_serializer import BrandSerializer
from astrobin_apps_equipment.models import EquipmentBrand


class BrandViewSet(viewsets.ModelViewSet):
    serializer_class = BrandSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [IsEquipmentModeratorOrReadOnly]
    filter_class = EquipmentBrandFilter
    http_method_names = ['get', 'post', 'head', 'put', 'patch']

    def get_queryset(self):
        return EquipmentBrand.objects.all()
