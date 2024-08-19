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
    listing_hash = serializers.SerializerMethodField()

    def is_list_view(self) -> bool:
        request = self.context.get('request')
        if request and 'hash' in request.query_params:
            return False
        return isinstance(self.root, serializers.ListSerializer)

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'item_object_id' in validated_data and validated_data['item_object_id'] is not None:
            validated_data['item_plain_text'] = None

        if 'item_plain_text' in validated_data and validated_data['item_plain_text'] is not None:
            validated_data['item_object_id'] = None

        if 'shipping_cost_type' in validated_data:
            if validated_data['shipping_cost_type'] == 'NO_SHIPPING':
                validated_data['shipping_cost'] = None
            elif validated_data['shipping_cost_type'] == 'COVERED_BY_SELLER':
                validated_data['shipping_cost'] = 0
            elif validated_data['shipping_cost_type'] == 'TO_BE_AGREED':
                validated_data['shipping_cost'] = None

        return super().update(instance, validated_data)

    def get_total_image_count(self, obj):
        if self.is_list_view():
            return None

        if obj.item_content_object is None:
            return 0

        return obj.item_content_object.image_count

    def get_seller_image_count(self, obj):
        if self.is_list_view():
            return None

        item = obj.item_content_object

        return Image.objects.filter(
            Q(user=obj.user) &
            Q(moderator_decision=ModeratorDecision.APPROVED) &
            self._get_equipment_query_for_image(item)
        ).count()

    def get_item_klass(self, obj):
        if obj.item_content_type is None:
            return None

        return obj.item_content_type.model.upper()

    def get_first_added_to_an_image(self, obj):
        if self.is_list_view():
            return None

        first_appeared_in_log_entry = None
        first_appeared_in_image = None

        log_entry = ImageEquipmentLog.objects.filter(
            equipment_item_content_type=obj.item_content_type,
            equipment_item_object_id=obj.item_object_id,
            image__user=obj.user,
        ).order_by('date').first()

        if log_entry:
            first_appeared_in_log_entry = log_entry.date

        image = Image.objects.filter(
            Q(user=obj.user) &
            Q(moderator_decision=ModeratorDecision.APPROVED) &
            self._get_equipment_query_for_image(obj.item_content_object)
        ).order_by('published').first()

        if image:
            first_appeared_in_image = image.published

        if first_appeared_in_log_entry is not None and first_appeared_in_image is not None:
            return min(first_appeared_in_log_entry, first_appeared_in_image)
        elif first_appeared_in_log_entry is not None:
            return first_appeared_in_log_entry
        elif first_appeared_in_image is not None:
            return first_appeared_in_image

        return None

    def get_listing_hash(self, obj):
        return obj.listing.hash if obj.listing else None

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

    def validate(self, attrs):
        item_object_id = attrs.get('item_object_id')
        item_plain_text = attrs.get('item_plain_text')

        # Ensure that both properties cannot be non-null at the same time
        if item_object_id is not None and item_plain_text is not None:
            raise serializers.ValidationError("You cannot provide both item_object_id and item_plain_text.")

        return attrs

    class Meta:
        model = EquipmentItemMarketplaceListingLineItem
        fields = '__all__'
        read_only_fields = ['id', 'hash', 'listing_hash', 'user', 'created', 'updated']
