from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import serializers

from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Image, ImageEquipmentLog
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_image_serializer import \
    EquipmentItemMarketplaceListingLineItemImageSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListingLineItem, Sensor
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass


class EquipmentItemMarketplaceListingLineItemSerializer(serializers.ModelSerializer):
    images = EquipmentItemMarketplaceListingLineItemImageSerializer(many=True, read_only=True)
    total_image_count = serializers.SerializerMethodField(read_only=True)
    seller_image_count = serializers.SerializerMethodField(read_only=True)
    item_klass = serializers.SerializerMethodField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_added_to_an_image = serializers.SerializerMethodField(read_only=True)
    slug = serializers.ReadOnlyField()

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    def get_total_image_count(self, obj):
        if obj.item_content_object is None:
            return 0

        return obj.item_content_object.image_count

    def get_seller_image_count(self, obj):
        item = obj.item_content_object

        return Image.objects.filter(
            Q(user=obj.user) &
            Q(moderator_decision=ModeratorDecision.APPROVED) &
            self._get_equipment_query_for_image(item)
        ).count()

    def get_item_klass(self, obj):
        if obj.item_content_object is None:
            return None
        return obj.item_content_object.klass

    def get_first_added_to_an_image(self, obj):
        log_entry = ImageEquipmentLog.objects.filter(
            equipment_item_content_type=obj.item_content_type,
            equipment_item_object_id=obj.item_object_id,
            image__user=obj.user,
        ).order_by('date').first()

        if log_entry:
            return log_entry.date

        image = Image.objects.filter(
            Q(user=obj.user) &
            Q(moderator_decision=ModeratorDecision.APPROVED) &
            self._get_equipment_query_for_image(obj.item_content_object)
        ).order_by('published').first()

        if image:
            return image.published

        return None

    def _get_equipment_query_for_image(self, item):
        if item is None:
            return Q()

        if item.klass == EquipmentItemKlass.TELESCOPE:
            return Q(imaging_telescopes_2=item) | Q(guiding_telescopes_2=item)
        elif item.klass == EquipmentItemKlass.CAMERA:
            return Q(imaging_cameras_2=item) | Q(guiding_cameras_2=item)
        elif item.klass == EquipmentItemKlass.SENSOR:
            return Q(imaging_cameras_2__sensor=item) | Q(guiding_cameras_2__sensor=item)
        elif item.klass == EquipmentItemKlass.MOUNT:
            return Q(mounts_2=item)
        elif item.klass == EquipmentItemKlass.FILTER:
            return Q(filters_2=item)
        elif item.klass == EquipmentItemKlass.ACCESSORY:
            return Q(accessories_2=item)
        elif item.klass == EquipmentItemKlass.SOFTWARE:
            return Q(software_2=item)

        return Q()

    def validate_year_of_purchase(self, value):
        if value is not None and value > datetime.now().year:
            raise serializers.ValidationError("Year of purchase must not be in the future.")

        return value

    def validate_item_content_type(self, value):
        if value is None:
            raise serializers.ValidationError("Item content type must be provided.")

        if value.id is ContentType.objects.get_for_model(Sensor).id:
            raise serializers.ValidationError("Sensors are not supported in the marketplace.")

        return value

    class Meta:
        model = EquipmentItemMarketplaceListingLineItem
        fields = '__all__'
        read_only_fields = ['id', 'hash', 'user', 'created', 'updated']
