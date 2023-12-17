from django.db.models import Q
from rest_framework import serializers

from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Image
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_image_serializer import \
    EquipmentItemMarketplaceListingLineItemImageSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListingLineItem
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass


class EquipmentItemMarketplaceListingLineItemSerializer(serializers.ModelSerializer):
    images = EquipmentItemMarketplaceListingLineItemImageSerializer(many=True, read_only=True)
    total_image_count = serializers.SerializerMethodField(read_only=True)
    seller_image_count = serializers.SerializerMethodField(read_only=True)
    item_klass = serializers.SerializerMethodField(read_only=True)

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    def get_total_image_count(self, obj):
        return obj.item_content_object.image_count

    def get_seller_image_count(self, obj):
        item = obj.item_content_object

        if item.klass == EquipmentItemKlass.TELESCOPE:
            q = Q(imaging_telescopes_2=item) | Q(guiding_telescopes_2=item)
        elif item.klass == EquipmentItemKlass.CAMERA:
            q = Q(imaging_cameras_2=item) | Q(guiding_cameras_2=item)
        elif item.klass == EquipmentItemKlass.MOUNT:
            q = Q(mounts_2=item)
        elif item.klass == EquipmentItemKlass.FILTER:
            q = Q(filters_2=item)
        elif item.klass == EquipmentItemKlass.ACCESSORY:
            q = Q(accessories_2=item)
        elif item.klass == EquipmentItemKlass.SOFTWARE:
            q = Q(software_2=item)
        else:
            q = Q()

        return Image.objects.filter(
            Q(user=obj.user) & Q(moderator_decision=ModeratorDecision.APPROVED) & q
        ).count()

    def get_item_klass(self, obj):
        return obj.item_content_object.klass

    class Meta:
        model = EquipmentItemMarketplaceListingLineItem
        fields = '__all__'
        read_only_fields = ['id', 'hash', 'user', 'created', 'updated']
