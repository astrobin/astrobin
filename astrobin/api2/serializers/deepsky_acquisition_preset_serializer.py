from astrobin.api2.serializers.acquisition_preset_serializer import AcquisitionPresetSerializer
from astrobin.models import DeepSky_Acquisition_Preset


class DeepSkyAcquisitionPresetSerializer(AcquisitionPresetSerializer):
    class Meta(AcquisitionPresetSerializer.Meta):
        abstract = False
        fields = [
            'name',
            'is_synthetic',
            'binning',
            'number',
            'duration',
            'iso',
            'gain',
            'f_number',
            'sensor_cooling',
            'darks',
            'flats',
            'flat_darks',
            'bias',
            'filter_2',
            'user',
        ]
        model = DeepSky_Acquisition_Preset
