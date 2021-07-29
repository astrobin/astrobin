from astrobin_apps_equipment.api.serializers.camera_serializer import CameraSerializer
from astrobin_apps_equipment.api.serializers.telescope_serializer import TelescopeSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class TelescopeViewSet(EquipmentItemViewSet):
    serializer_class = TelescopeSerializer

