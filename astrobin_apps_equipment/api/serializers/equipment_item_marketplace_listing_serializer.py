from hitcount.models import HitCount
from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_read_serializer import \
    EquipmentItemMarketplaceListingLineItemReadSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing
from toggleproperties.models import ToggleProperty


class EquipmentItemMarketplaceListingSerializer(serializers.ModelSerializer):
    line_items = EquipmentItemMarketplaceListingLineItemReadSerializer(many=True, read_only=True)
    follower_count = serializers.SerializerMethodField(read_only=True)
    view_count = serializers.SerializerMethodField(read_only=True)
    hitcount_pk = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    def get_follower_count(self, obj):
        return ToggleProperty.objects.toggleproperties_for_object('follow', obj).count()

    def get_view_count(self, obj):
        return HitCount.objects.get_for_object(obj).hits

    def get_hitcount_pk(self, obj):
        return HitCount.objects.get_for_object(obj).pk

    class Meta:
        model = EquipmentItemMarketplaceListing
        fields = '__all__'
        read_only_fields = [
            'id',
            'hash',
            'user',
            'created',
            'updated',
        ]
