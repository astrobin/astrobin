from rest_framework import serializers

from astrobin_apps_iotd.models import IotdStaffMemberSettings
from common.mixins import RequestUserRestSerializerMixin


class StaffMemberSettingsSerializer(RequestUserRestSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = IotdStaffMemberSettings
        fields = '__all__'
