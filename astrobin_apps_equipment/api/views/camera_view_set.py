from astrobin_apps_equipment.api.serializers.camera_serializer import CameraSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet
from astrobin_apps_equipment.models import Camera


class CameraViewSet(EquipmentItemViewSet):
    serializer_class = CameraSerializer

    def get_queryset(self):
        return Camera.objects.all()
