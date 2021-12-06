from astrobin_apps_equipment.api.filters.filter_filter import FilterFilter
from astrobin_apps_equipment.api.serializers.filter_image_serializer import FilterImageSerializer
from astrobin_apps_equipment.api.serializers.filter_serializer import FilterSerializer
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class FilterViewSet(EquipmentItemViewSet):
    serializer_class = FilterSerializer
    filter_class = FilterFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=FilterImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(FilterViewSet, self).image_upload(request, pk)
