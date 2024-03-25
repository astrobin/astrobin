from rest_framework import serializers

from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem,
    EquipmentItemMarketplaceOffer,
)
from common.mixins import RequestUserRestSerializerMixin


class EquipmentItemMarketplaceOfferSerializer(RequestUserRestSerializerMixin, serializers.ModelSerializer):
    listing = serializers.PrimaryKeyRelatedField(queryset=EquipmentItemMarketplaceListing.objects.all())
    line_item = serializers.PrimaryKeyRelatedField(queryset=EquipmentItemMarketplaceListingLineItem.objects.all())
    user_display_name = serializers.SerializerMethodField(read_only=True)

    def get_user_display_name(self, obj: EquipmentItemMarketplaceOffer):
        return obj.user.userprofile.get_display_name()

    class Meta:
        model = EquipmentItemMarketplaceOffer
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created', 'updated']
