from rest_framework import serializers

from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem,
    EquipmentItemMarketplaceOffer,
)
from common.mixins import RequestUserRestSerializerMixin


class EquipmentItemMarketplaceOfferSerializer(RequestUserRestSerializerMixin, serializers.ModelSerializer):
    listing = serializers.PrimaryKeyRelatedField(queryset=EquipmentItemMarketplaceListing.objects.all())
    line_item = serializers.PrimaryKeyRelatedField(queryset=EquipmentItemMarketplaceListingLineItem.objects.all())
    user_name = serializers.SerializerMethodField(read_only=True)
    user_display_name = serializers.SerializerMethodField(read_only=True)
    line_item_display_name = serializers.SerializerMethodField(read_only=True)

    def get_user_name(self, obj: EquipmentItemMarketplaceOffer):
        return obj.user.username

    def get_user_display_name(self, obj: EquipmentItemMarketplaceOffer):
        return obj.user.userprofile.get_display_name()

    def get_line_item_display_name(self, obj: EquipmentItemMarketplaceOffer):
        return obj.line_item.item_name or obj.line_item.item_plain_text

    def update(self, instance, validated_data):
        # Check if master_offer_uuid is being updated
        if 'master_offer_uuid' in validated_data and instance.master_offer_uuid != validated_data['master_offer_uuid']:
            raise serializers.ValidationError("The field master_offer_uuid cannot be updated.")

        return super().update(instance, validated_data)

    class Meta:
        model = EquipmentItemMarketplaceOffer
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created', 'updated']
