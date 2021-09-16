from astrobin_apps_equipment.api.filters.camera_filter import CameraFilter
from astrobin_apps_equipment.models import CameraEditProposal


class CameraEditProposalFilter(CameraFilter):
    class Meta(CameraFilter.Meta):
        model = CameraEditProposal
