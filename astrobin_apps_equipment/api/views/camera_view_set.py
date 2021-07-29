from astrobin_apps_equipment.api.serializers.camera_serializer import CameraSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class CameraViewSet(EquipmentItemViewSet):
    serializer_class = CameraSerializer

