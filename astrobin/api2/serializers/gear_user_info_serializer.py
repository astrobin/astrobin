from rest_framework import serializers

from astrobin.models import GearUserInfo


class GearUserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GearUserInfo
        fields = '__all__'
