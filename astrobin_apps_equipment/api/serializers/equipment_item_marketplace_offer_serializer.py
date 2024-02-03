from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceOffer
from common.mixins import RequestUserRestSerializerMixin


class EquipmentItemMarketplaceOfferSerializer(
    RequestUserRestSerializerMixin, serializers.ModelSerializer
):
    def validate_user(self, value):
        return self.context['request'].user

    class Meta:
        model = EquipmentItemMarketplaceOffer
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created', 'updated']
