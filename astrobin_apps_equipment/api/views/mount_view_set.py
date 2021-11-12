from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.mount_filter import MountFilter
from astrobin_apps_equipment.api.serializers.mount_image_serializer import MountImageSerializer
from astrobin_apps_equipment.api.serializers.mount_serializer import MountSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class MountViewSet(EquipmentItemViewSet):
    serializer_class = MountSerializer
    filter_class = MountFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=MountImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(MountViewSet, self).image_upload(request, pk)
