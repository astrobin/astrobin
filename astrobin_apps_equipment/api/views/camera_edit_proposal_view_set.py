from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.camera_edit_proposal_filter import CameraEditProposalFilter
from astrobin_apps_equipment.api.serializers.camera_edit_proposal_image_serializer import \
    CameraEditProposalImageSerializer
from astrobin_apps_equipment.api.serializers.camera_edit_proposal_serializer import CameraEditProposalSerializer
from astrobin_apps_equipment.api.serializers.camera_image_serializer import CameraImageSerializer
from astrobin_apps_equipment.api.views.equipment_item_edit_proposal_view_set import EquipmentItemEditProposalViewSet


class CameraEditProposalViewSet(EquipmentItemEditProposalViewSet):
    serializer_class = CameraEditProposalSerializer
    filter_class = CameraEditProposalFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=CameraEditProposalImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(CameraEditProposalViewSet, self).image_upload(request, pk)

    class Meta(EquipmentItemEditProposalViewSet.Meta):
        abstract = False
