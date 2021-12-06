from django.db.models.functions import Lower
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.camera_filter import CameraFilter
from astrobin_apps_equipment.api.serializers.camera_image_serializer import CameraImageSerializer
from astrobin_apps_equipment.api.serializers.camera_serializer import CameraSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class CameraViewSet(EquipmentItemViewSet):
    serializer_class = CameraSerializer
    filter_class = CameraFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        sort = self.request.GET.get('sort')

        if sort == 'az':
            queryset = queryset.order_by(Lower('brand__name'), Lower('name'), 'modified')

        return queryset

    @action(
        detail=True,
        methods=['post'],
        serializer_class=CameraImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(CameraViewSet, self).image_upload(request, pk)
