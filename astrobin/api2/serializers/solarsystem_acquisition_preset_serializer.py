from astrobin.api2.serializers.acquisition_preset_serializer import AcquisitionPresetSerializer
from astrobin.models import SolarSystem_Acquisition_Preset


class SolarSystemAcquisitionPresetSerializer(AcquisitionPresetSerializer):
    class Meta(AcquisitionPresetSerializer.Meta):
        abstract = False
        fields = [
            'id',
            'name',
            'frames',
            'fps',
            'exposure_per_frame',
            'focal_length',
            'user',
        ]
        model = SolarSystem_Acquisition_Preset
