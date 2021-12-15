from astrobin.api2.serializers.gear_serializer import GearSerializer
from astrobin.models import FocalReducer


class FocalReducerSerializer(GearSerializer):
    class Meta(GearSerializer.Meta):
        model = FocalReducer
        fields = GearSerializer.Meta.fields
